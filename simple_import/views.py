from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from simple_import.models import ImportLog, ImportSetting

class ImportForm(forms.ModelForm):
    class Meta:
        model = ImportLog
        fields = ('name', 'import_file',)
    model = forms.ModelChoiceField(ContentType.objects.all())
    

def start_import(request):
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
    else:
        form = ImportForm()
    if not request.user.is_superuser:
        form.fields["model"].queryset = ContentType.objects.filter(
            Q(permission__group__user=request.user, permission__codename__startswith="change_") |
            Q(permission__user=request.user, permission__codename__startswith="change_")).distinct()
    
    return render_to_response('simple_import/import.html', {'form':form,}, RequestContext(request, {}),)

def match_columns(request):
    pass
