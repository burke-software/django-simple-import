from django import forms
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.db.models import Q, ForeignKey
from django.db import transaction
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
import sys
from django.db.models.fields import AutoField
from django.utils.encoding import smart_text

from simple_import.compat import User
from simple_import.models import ImportLog, ImportSetting, ColumnMatch, ImportedObject, RelationalMatch
from simple_import.forms import ImportForm, MatchForm, MatchRelationForm


if sys.version_info >= (3,0):
    unicode = str

def validate_match_columns(import_log, model_class, header_row):
    """ Perform some basic pre import validation to make sure it's
    even possible the import can work
    Returns list of errors
    """
    errors = []
    column_matches = import_log.import_setting.columnmatch_set.all()
    field_names = model_class._meta.get_all_field_names()
    for field_name in field_names:
        field_object, model, direct, m2m = model_class._meta.get_field_by_name(field_name)
        # Skip if update only and skip ptr which suggests it's a django inherited field
        # Also some hard coded ones for Django Auth
        if import_log.import_type != "O" and field_name[-3:] != "ptr" and \
            not field_name in ['password', 'date_joined', 'last_login']: 
            if (direct and model and not field_object.blank) or (not getattr(field_object, "blank", True)):
                field_matches = column_matches.filter(field_name=field_name)
                match_in_header = False
                if field_matches:
                    for field_match in field_matches:
                        if field_match.column_name.lower() in header_row:
                            match_in_header = True
                    if not match_in_header:
                        errors += [u"{0} is required but is not in your spreadsheet. ".format(field_object.verbose_name.title())]
                else:
                    errors += [u"{0} is required but has no match.".format(field_object.verbose_name.title())]
    return errors


def get_custom_fields_from_model(model_class):
    """ django-custom-fields support
    """
    if 'custom_field' in settings.INSTALLED_APPS:
        from custom_field.models import CustomField
        try:
            content_type = ContentType.objects.get(model=model_class._meta.module_name,app_label=model_class._meta.app_label)
        except ContentType.DoesNotExist:
            content_type = None
        custom_fields = CustomField.objects.filter(content_type=content_type)
        return custom_fields


@staff_member_required
def match_columns(request, import_log_id):
    """ View to match import spreadsheet columns with database fields
    """
    import_log = get_object_or_404(ImportLog, id=import_log_id)
    
    if not request.user.is_superuser and import_log.user != request.user:
        raise SuspiciousOperation("Non superuser attempting to view other users import")
    
    # need to generate matches if they don't exist already
    existing_matches = import_log.get_matches()
    
    MatchFormSet = inlineformset_factory(ImportSetting, ColumnMatch, form=MatchForm, extra=0)
    
    import_data = import_log.get_import_file_as_list()
    header_row = [x.lower() for x in import_data[0]] # make all lower 
    try:
        sample_row = import_data[1]
    except IndexError:
        messages.error(request, 'Error: Spreadsheet was empty.')
        return redirect('simple_import-start_import')
       
    errors = []
    
    model_class = import_log.import_setting.content_type.model_class()
    field_names = model_class._meta.get_all_field_names()
    for field_name in field_names:
        field_object, model, direct, m2m = model_class._meta.get_field_by_name(field_name)
        # We can't add a new AutoField and specify it's value
        if import_log.import_type == "N" and isinstance(field_object, AutoField):
            field_names.remove(field_name)
        
    if request.method == 'POST':
        formset = MatchFormSet(request.POST, instance=import_log.import_setting)
        if formset.is_valid():
            formset.save()
            if import_log.import_type in ["U", "O"]:
                update_key = request.POST.get('update_key', '')
                
                if update_key:
                    field_name = import_log.import_setting.columnmatch_set.get(column_name=update_key).field_name
                    if field_name:
                        field_object, model, direct, m2m = model_class._meta.get_field_by_name(field_name)
                        
                        if direct and field_object.unique:
                            import_log.update_key = update_key
                            import_log.save()
                        else:
                            errors += ['Update key must be unique. Please select a unique field.']
                    else:
                        errors += ['Update key must matched with a column.']
                else:
                    errors += ['Please select an update key. This key is used to linked records for updating.']
            errors += validate_match_columns(
                import_log,
                model_class,
                header_row)
            
            all_field_names = []
            for clean_data in formset.cleaned_data:
                if clean_data['field_name']:
                    if clean_data['field_name'] in all_field_names:
                        errors += ["{0} is duplicated.".format(clean_data['field_name'])]
                    all_field_names += [clean_data['field_name']]
            if not errors:
                return HttpResponseRedirect(reverse(
                    match_relations,
                    kwargs={'import_log_id': import_log.id}))
    else:
        formset = MatchFormSet(instance=import_log.import_setting, queryset=existing_matches)
    
    field_choices = (('', 'Do Not Use'),)
    for field_name in field_names:
        field_object, model, direct, m2m = model_class._meta.get_field_by_name(field_name)
        add = True
        
        if direct:
            field_verbose = field_object.verbose_name
        else:
            field_verbose = field_name
        
        if direct and  not field_object.blank:
            field_verbose += " (Required)"
        if direct and field_object.unique:
            field_verbose += " (Unique)"
        if m2m or isinstance(field_object, ForeignKey):
            field_verbose += " (Related)"
        elif not direct:
            add = False
        
        if add:
            field_choices += ((field_name, field_verbose),)
    
    # Include django-custom-field support
    custom_fields = get_custom_fields_from_model(model_class)
    if custom_fields:
        for custom_field in custom_fields:
            field_choices += (("simple_import_custom__{0}".format(custom_field),
                           "{0} (Custom)".format(custom_field)),)
    # Include defined methods
    # Model must have a simple_import_methods defined
    if hasattr(model_class, 'simple_import_methods'):
        for import_method in model_class.simple_import_methods:
            field_choices += (("simple_import_method__{0}".format(import_method),
                               "{0} (Method)".format(import_method)),)
    # User model should allow set password
    if issubclass(model_class, User):
        field_choices += (("simple_import_method__{0}".format('set_password'),
                               "Set Password (Method)"),) 
    
    for i, form in enumerate(formset):
        form.fields['field_name'].widget = forms.Select(choices=(field_choices))
        form.sample = sample_row[i]
    
    return render_to_response(
        'simple_import/match_columns.html',
        {'import_log': import_log, 'formset': formset, 'errors': errors},
        RequestContext(request, {}),)


def get_direct_fields_from_model(model_class):
    direct_fields = []
    all_fields_names = model_class._meta.get_all_field_names()
    for field_name in all_fields_names:
        field = model_class._meta.get_field_by_name(field_name)
        # Direct, not m2m, not FK
        if field[2] and not field[3] and field[0].__class__.__name__ != "ForeignKey":
            direct_fields += [field[0]]
    return direct_fields


@staff_member_required
def match_relations(request, import_log_id):
    import_log = get_object_or_404(ImportLog, id=import_log_id)
    model_class = import_log.import_setting.content_type.model_class()
    matches = import_log.get_matches()
    field_names = []
    choice_set = []
    
    for match in matches.exclude(field_name=""):
        field_name = match.field_name
        
        if not field_name.startswith('simple_import_custom__') and \
                not field_name.startswith('simple_import_method__'):
            field, model, direct, m2m = model_class._meta.get_field_by_name(field_name)
            
            if m2m or isinstance(field, ForeignKey): 
                RelationalMatch.objects.get_or_create(
                    import_log=import_log,
                    field_name=field_name)
                
                field_names.append(field_name)
                choices = ()
                if hasattr(field, 'related'):
                    parent_model = field.related.parent_model()
                else:
                    parent_model = field.parent_model()
                for field in get_direct_fields_from_model(parent_model):
                    if field.unique:
                        choices += ((field.name, unicode(field.verbose_name)),)
                choice_set += [choices]
    
    existing_matches = import_log.relationalmatch_set.filter(field_name__in=field_names)
    
    MatchRelationFormSet = inlineformset_factory(
        ImportLog,
        RelationalMatch,
        form=MatchRelationForm, extra=0)
    
    if request.method == 'POST':
        formset = MatchRelationFormSet(request.POST, instance=import_log)
        
        if formset.is_valid():
            formset.save()
            
            url = reverse('simple_import-do_import',
                kwargs={'import_log_id': import_log.id})
            
            if 'commit' in request.POST:
                url += "?commit=True"
            
            return HttpResponseRedirect(url)
    else:
        formset = MatchRelationFormSet(instance=import_log)
    
    for i, form in enumerate(formset.forms):
        choices = choice_set[i]
        form.fields['related_field_name'].widget = forms.Select(choices=choices)
    
    return render_to_response(
        'simple_import/match_relations.html',
        {'formset': formset,
         'existing_matches': existing_matches},
        RequestContext(request, {}),)

def set_field_from_cell(import_log, new_object, header_row_field_name, cell):
    """ Set a field from a import cell. Use referenced fields the field
    is m2m or a foreign key.
    """
    if (not header_row_field_name.startswith('simple_import_custom__') and
            not header_row_field_name.startswith('simple_import_method__')):
        field, model, direct, m2m =  new_object._meta.get_field_by_name(header_row_field_name)
        if m2m:
            new_object.simple_import_m2ms[header_row_field_name] = cell
        elif isinstance(field, ForeignKey):
            related_field_name = RelationalMatch.objects.get(import_log=import_log, field_name=field.name).related_field_name
            related_model = field.related.parent_model
            related_object = related_model.objects.get(**{related_field_name:cell})
            setattr(new_object, header_row_field_name, related_object)
        elif field.choices and getattr(settings, 'SIMPLE_IMPORT_LAZY_CHOICES', True):
            # Prefer database values over choices lookup
            database_values, verbose_values = zip(*field.choices)
            if cell in database_values:
                setattr(new_object, header_row_field_name, cell)
            elif cell in verbose_values:
                for choice in field.choices:
                    if smart_text(cell) == smart_text(choice[1]):
                        setattr(new_object, header_row_field_name, choice[0])
        else:
            setattr(new_object, header_row_field_name, cell)
    
    
def set_method_from_cell(import_log, new_object, header_row_field_name, cell):
    """ Run a method from a import cell.
    """
    if (not header_row_field_name.startswith('simple_import_custom__') and
            not header_row_field_name.startswith('simple_import_method__')):
        pass
    elif header_row_field_name.startswith('simple_import_custom__'):
        new_object.set_custom_value(header_row_field_name[22:], cell)
    elif header_row_field_name.startswith('simple_import_method__'):
        getattr(new_object, header_row_field_name[22:])(cell)
       

@staff_member_required
def do_import(request, import_log_id):
    """ Import the data!
    """
    import_log = get_object_or_404(ImportLog, id=import_log_id)
    if import_log.import_type == "N" and 'undo' in request.GET and request.GET['undo'] == "True":
        import_log.undo()
        return HttpResponseRedirect(reverse(
                    do_import,
                    kwargs={'import_log_id': import_log.id}) + '?success_undo=True')
    
    if 'success_undo' in request.GET and request.GET['success_undo'] == "True":
        success_undo = True
    else:
        success_undo = False
    
    model_class = import_log.import_setting.content_type.model_class()
    import_data = import_log.get_import_file_as_list()
    header_row = import_data.pop(0)
    header_row_field_names = []
    header_row_default = []
    header_row_null_on_empty = []
    error_data = [header_row + ['Error Type', 'Error Details']]
    create_count = 0
    update_count = 0
    fail_count = 0
    if 'commit' in request.GET and request.GET['commit'] == "True":
        commit = True
    else:
        commit = False
    
    key_column_name = None
    if import_log.update_key and import_log.import_type in ["U", "O"]:
        key_match = import_log.import_setting.columnmatch_set.get(column_name=import_log.update_key)
        key_column_name = key_match.column_name
        key_field_name = key_match.field_name
    for i, cell in enumerate(header_row):
        match = import_log.import_setting.columnmatch_set.get(column_name=cell)
        header_row_field_names += [match.field_name]
        header_row_default += [match.default_value]
        header_row_null_on_empty += [match.null_on_empty]
        if key_column_name == cell.lower():
            key_index = i
    
    with transaction.commit_manually():
        for row in import_data:
            try:
                is_created = True
                if import_log.import_type == "N":
                    new_object = model_class()
                elif import_log.import_type == "O":
                    filters = {key_field_name: row[key_index]}
                    new_object = model_class.objects.get(**filters)
                    is_created = False
                elif import_log.import_type == "U":
                    filters = {key_field_name: row[key_index]}
                    try:
                        new_object = model_class.objects.get(**filters)
                        is_created = False
                    except model_class.DoesNotExist:
                        new_object = model_class()
                new_object.simple_import_m2ms = {} # Need to deal with these after saving
                for i, cell in enumerate(row):
                    if header_row_field_names[i]: # skip blank
                        if not import_log.is_empty(cell) or header_row_null_on_empty[i]:
                            set_field_from_cell(import_log, new_object, header_row_field_names[i], cell)
                        elif header_row_default[i]:
                            set_field_from_cell(import_log, new_object, header_row_field_names[i], header_row_default[i])
                new_object.save()

                for i, cell in enumerate(row):
                    if header_row_field_names[i]: # skip blank
                        if not import_log.is_empty(cell) or header_row_null_on_empty[i]:
                            set_method_from_cell(import_log, new_object, header_row_field_names[i], cell)
                        elif header_row_default[i]:
                            set_method_from_cell(import_log, new_object, header_row_field_names[i], header_row_default[i])
                # set_custom_value() calls save() on its own, but the same cannot be assumed
                # for other methods, e.g. set_password()
                new_object.save()

                for key in new_object.simple_import_m2ms.keys():
                    value = new_object.simple_import_m2ms[key]
                    m2m = getattr(new_object, key)
                    m2m_model = type(m2m.model())
                    related_field_name = RelationalMatch.objects.get(import_log=import_log, field_name=key).related_field_name
                    m2m_object = m2m_model.objects.get(**{related_field_name:value})
                    m2m.add(m2m_object)
                
                if is_created:
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk, 
                        content_type_id = ContentType.objects.get_for_model(new_object).pk,
                        object_id       = new_object.pk,
                        object_repr     = smart_text(new_object), 
                        action_flag     = ADDITION
                    )
                    create_count += 1
                else:
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk, 
                        content_type_id = ContentType.objects.get_for_model(new_object).pk,
                        object_id       = new_object.pk,
                        object_repr     = smart_text(new_object), 
                        action_flag     = CHANGE
                    )
                    update_count += 1
                ImportedObject.objects.create(
                    import_log = import_log,
                    object_id = new_object.pk,
                    content_type = import_log.import_setting.content_type)
            except IntegrityError:
                exc = sys.exc_info()
                error_data += [row + ["Integrity Error", smart_text(exc[1][1])]]
                fail_count += 1
            except ObjectDoesNotExist:
                exc = sys.exc_info()
                error_data += [row + ["No Record Found to Update", smart_text(exc[1])]]
                fail_count += 1
            except ValueError:
                exc = sys.exc_info()
                if unicode(exc[1]).startswith('invalid literal for int() with base 10'):
                    error_data += [row + ["Incompatible Data - A number was expected, but a character was used", smart_text(exc[1])]] 
                else:
                    error_data += [row + ["Value Error", smart_text(exc[1])]]
                fail_count += 1
            except:
                exc = sys.exc_info()
                error_data += [row + ["Unknown Error", smart_text(exc[1])]]
                fail_count += 1
        if commit:
            transaction.commit()
        else:
            transaction.rollback()
    
            
    if fail_count:
        from io import StringIO
        from django.core.files.base import ContentFile
        from openpyxl.workbook import Workbook
        from openpyxl.writer.excel import save_virtual_workbook
        
        wb = Workbook()
        ws = wb.worksheets[0]
        ws.title = "Errors"
        filename = 'Errors.xlsx'
        for row in error_data:
            ws.append(row)
        buf = StringIO()
        # Not Python 3 compatible 
        #buf.write(str(save_virtual_workbook(wb)))
        import_log.error_file.save(filename, ContentFile(save_virtual_workbook(wb)))
        import_log.save()
    
    return render_to_response(
        'simple_import/do_import.html',
        {
            'error_data': error_data,
            'create_count': create_count,
            'update_count': update_count,
            'fail_count': fail_count,
            'import_log': import_log,
            'commit': commit,
            'success_undo': success_undo,},
        RequestContext(request, {}),)


@staff_member_required
def start_import(request):
    """ View to create a new import record
    """
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            import_log = form.save(commit=False)
            import_log.user = request.user
            import_log.import_setting, created = ImportSetting.objects.get_or_create(
                user=request.user,
                content_type=form.cleaned_data['model'],
            )
            import_log.save()
            return HttpResponseRedirect(reverse(match_columns, kwargs={'import_log_id': import_log.id}))
    else:
        form = ImportForm()
    if not request.user.is_superuser:
        form.fields["model"].queryset = ContentType.objects.filter(
            Q(permission__group__user=request.user, permission__codename__startswith="change_") |
            Q(permission__user=request.user, permission__codename__startswith="change_")).distinct()
    
    return render_to_response('simple_import/import.html', {'form':form,}, RequestContext(request, {}),)

