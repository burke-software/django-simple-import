from django import forms
from django.contrib.contenttypes.models import ContentType

from simple_import.models import ImportLog, ColumnMatch


class ImportForm(forms.ModelForm):
    class Meta:
        model = ImportLog
        fields = ('name', 'import_file', 'import_type')
    model = forms.ModelChoiceField(ContentType.objects.all())
    
    
class MatchForm(forms.ModelForm):
    class Meta:
        model = ColumnMatch