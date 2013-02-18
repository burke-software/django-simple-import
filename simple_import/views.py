from django import forms
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db import transaction
from django.db import IntegrityError
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
import sys

from simple_import.models import ImportLog, ImportSetting, ColumnMatch, ImportedObject
from simple_import.forms import ImportForm, MatchForm

def validate_match_columns(import_log, field_names, model_class, header_row):
    """ Perform some basic pre import validation to make sure it's
    even possible the import can work
    Returns list of errors
    """
    errors = []
    column_matches = import_log.import_setting.columnmatch_set.all()
    for field_name in field_names:
        field_object, model, direct, m2m = model_class._meta.get_field_by_name(field_name)
        if (direct and
            model and
            not field_object.blank):
            field_matches = column_matches.filter(field_name=field_name)
            if field_matches:
                if field_matches[0].column_name not in header_row:
                    errors += ["{0} is required but is not in your spreadsheet. ".format(field_object.verbose_name)]
            else:
                errors += ["{0} is required but has no match.".format(field_object.verbose_name)]
    
    return errors

@staff_member_required
def match_columns(request, import_log_id):
    """ View to match import spreadsheet columns with database fields
    """
    import_log = get_object_or_404(ImportLog, id=import_log_id)
    if not request.user.is_superuser and import_log.user != request.user:
        raise SuspiciousOperation("Non superuser attempting to view other users import")
    
    MatchFormSet = modelformset_factory(ColumnMatch, form=MatchForm, extra=0)
    import_data = import_log.get_import_file_as_list()
    header_row = import_data[0]
    sample_row = import_data[1]
    errors = []
    
    model_class = import_log.import_setting.content_type.model_class()
    field_names = model_class._meta.get_all_field_names()
        
    if request.POST:
        formset = MatchFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            errors += validate_match_columns(
                import_log,
                field_names,
                model_class,
                header_row)
            all_field_names = []
            for clean_data in formset.cleaned_data:
                if clean_data['field_name']:
                    if clean_data['field_name'] in all_field_names:
                        errors += ["{0} is duplicated.".format(clean_data['field_name'])]
                    all_field_names += [clean_data['field_name']]
            if not errors:
                get = ''
                if 'commit' in request.POST:
                    get = "?commit=True"
                return HttpResponseRedirect(reverse(
                    do_import,
                    kwargs={'import_log_id': import_log.id}) + get)
    else:
        match_ids = []
        for cell in header_row:
            try:
                match = ColumnMatch.objects.get(
                    import_setting = import_log.import_setting,
                    column_name = cell,
                )
            except ColumnMatch.DoesNotExist:
                match = ColumnMatch(
                    import_setting = import_log.import_setting,
                    column_name = cell,
                )
                match.guess_field()
                match.save()
            match_ids += [match.id]
        
        existing_matches = ColumnMatch.objects.filter(id__in=match_ids)
        formset = MatchFormSet(queryset=existing_matches)
        
    field_choices = (('', 'Do Not Use'),)
    for field_name in field_names:
        field_object, model, direct, m2m = model_class._meta.get_field_by_name(field_name)
        
        if direct:
            field_verbose = field_object.verbose_name
        else:
            field_verbose = field_name
        
        if direct and model and not field_object.blank:
            field_verbose += " (Required)"
        if direct and field_object.unique:
            field_verbose += " (Unique)"
        
        field_choices += ((field_name, field_verbose),)
    
    i = 0
    for form in formset:
        form.fields['field_name'].widget = forms.Select(choices=(field_choices))
        form.sample = sample_row[i]
        i += 1
    
    return render_to_response(
        'simple_import/match_columns.html',
        {'formset':formset, 'errors': errors},
        RequestContext(request, {}),)


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
    error_data = [header_row + ['Error Type', 'Error Details']]
    create_count = 0
    fail_count = 0
    if 'commit' in request.GET and request.GET['commit'] == "True":
        commit = True
    else:
        commit = False
    
    for cell in header_row:
        match = import_log.import_setting.columnmatch_set.get(column_name=cell)
        header_row_field_names += [match.field_name]
    
    with transaction.commit_manually():
        for row in import_data:
            try:
                new_object = model_class()
                for i, cell in enumerate(row):
                    setattr(new_object, header_row_field_names[i], cell)
                new_object.save()
                create_count += 1
                ImportedObject.objects.create(
                    import_log = import_log,
                    object_id = new_object.pk,
                    content_type = import_log.import_setting.content_type)
            except IntegrityError:
                exc = sys.exc_info()
                error_data += [row + ["Integrity Error", unicode(exc[1][1])]]
                fail_count += 1
            except:
                exc = sys.exc_info()
                error_data += [row + ["Unknown Error", unicode(exc[1])]]
                fail_count += 1
        if commit:
            transaction.commit()
        else:
            transaction.rollback()
    
            
    if fail_count:
        import cStringIO as StringIO
        from django.core.files.base import ContentFile
        from openpyxl.workbook import Workbook
        from openpyxl.writer.excel import save_virtual_workbook
        from openpyxl.cell import get_column_letter
        import re
        
        wb = Workbook()
        ws = wb.worksheets[0]
        ws.title = "Errors"
        filename = 'Errors.xlsx'
        for row in error_data:
            ws.append(row)
        buf = StringIO.StringIO()
        buf.write(save_virtual_workbook(wb))
        import_log.error_file.save(filename, ContentFile(buf.getvalue()))
        import_log.save()
    
    return render_to_response(
        'simple_import/do_import.html',
        {
            'error_data': error_data,
            'create_count': create_count,
            'fail_count': fail_count,
            'import_log': import_log,
            'commit': commit,
            'success_undo': success_undo,},
        RequestContext(request, {}),)


@staff_member_required
def start_import(request):
    """ View to create a new import record
    """
    if request.POST:
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            import_log = form.save(commit=False)
            import_log.user = request.user
            import_log.import_setting, created = ImportSetting.objects.get_or_create(
                user=request.user,
                content_type=ContentType.objects.get(id=form.data['model']),
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
