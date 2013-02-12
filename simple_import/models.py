from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models

class ImportSetting(models.Model):
    """ Save some settings per user per content type """
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    
class ColumnMatch(models.Model):
    """ Match column names from the user uploaded file to the database """
    column_name = models.CharField(max_length=255)
    field_name = models.CharField(max_length=255)
    import_setting = models.ForeignKey(ImportSetting)
    
class ImportLog(models.Model):
    """ A log of all import attempts """
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, editable=False, related_name="simple_import_log")
    date = models.DateTimeField(auto_now_add=True)
    import_file = models.FileField(upload_to="import_file")
    error_file = models.FileField(upload_to="error_file", blank=True)
    import_setting = models.ForeignKey(ImportSetting, editable=False)
    def __unicode__(self):
        return unicode(self.name)