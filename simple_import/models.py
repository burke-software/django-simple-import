from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.conf import settings
from django.db import transaction

class ImportSetting(models.Model):
    """ Save some settings per user per content type """
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    
class ColumnMatch(models.Model):
    """ Match column names from the user uploaded file to the database """
    column_name = models.CharField(max_length=200)
    field_name = models.CharField(max_length=255, blank=True)
    import_setting = models.ForeignKey(ImportSetting)
    default_value = models.CharField(max_length=2000, blank=True)
    null_on_empty = models.BooleanField(help_text="If cell is blank, clear out the field setting it to blank.")
    header_position = models.IntegerField(help_text="Annoying way to order the columns to match the header rows")
    
    class Meta:
        unique_together = ('column_name', 'import_setting')
    
    def __unicode__(self):
        return unicode('{0} {1}'.format(self.column_name, self.field_name))
    
    def guess_field(self):
        """ Guess the match based on field names
        First look for an exact field name match
        then search defined alternative names
        then normalize the field name and check for match
        """
        model = self.import_setting.content_type.model_class()
        field_names = model._meta.get_all_field_names()
        if self.column_name in field_names:
            self.field_name = self.column_name
            return
        #TODO user defined alt names
        normalized_field_name = self.column_name.lower().replace(' ', '_')
        if normalized_field_name in field_names:
            self.field_name = self.column_name
        # Try verbose name
        for field_name in field_names:
            field = model._meta.get_field_by_name(field_name)[0]
            if hasattr(field, 'verbose_name'):
                if field.verbose_name.lower().replace(' ', '_') == normalized_field_name:
                    self.field_name = field_name
            

    
class ImportLog(models.Model):
    """ A log of all import attempts """
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, editable=False, related_name="simple_import_log")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    import_file = models.FileField(upload_to="import_file")
    error_file = models.FileField(upload_to="error_file", blank=True)
    import_setting = models.ForeignKey(ImportSetting, editable=False)
    import_type_choices = (
        ("N", "Create New Records"),
        ("U", "Create and Update Records"),
        ("O", "Only Update Records"),
    )
    import_type = models.CharField(max_length=1, choices=import_type_choices)
    update_key = models.CharField(max_length=200, blank=True)
    
    def __unicode__(self):
        return unicode(self.name)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        filename = str(self.import_file).lower()
        if not filename[-3:] in ('xls', 'ods', 'csv', 'lsx'):
            raise ValidationError('Invalid file type. Must be xls, xlsx, ods, or csv.')
    
    @transaction.commit_on_success
    def undo(self):
        if self.import_type != "N":
            raise Exception("Cannot undo this type of import!")
        for obj in self.importedobject_set.all():
            if obj.content_object:
                obj.content_object.delete()
            obj.delete()
    
    def get_matches(self):
        """ Get each matching header row to database match
        Returns a ColumnMatch queryset"""
        header_row = self.get_import_file_as_list(only_header=True)
        matches = ColumnMatch.objects.none()
        match_ids = []
        for i, cell in enumerate(header_row):
            if cell: # Sometimes we get blank headers, ignore them.
                try:
                    match = ColumnMatch.objects.get(
                        import_setting = self.import_setting,
                        column_name = cell,
                    )
                except ColumnMatch.DoesNotExist:
                    match = ColumnMatch(
                        import_setting = self.import_setting,
                        column_name = cell,
                    )
                    match.guess_field()
                match.header_position = i
                match.save()
                match_ids += [match.id]
        return ColumnMatch.objects.filter(pk__in=match_ids).order_by('header_position')

    def get_import_file_as_list(self, only_header=False):
        file_ext = str(self.import_file).lower()[-3:]
        data = []
        if file_ext == "xls":
            import xlrd
            import os
            wb = xlrd.open_workbook(os.path.join(settings.MEDIA_ROOT, self.import_file.file.name))
            sh1 = wb.sheet_by_index(0)
            for rownum in range(sh1.nrows): 
                data += [sh1.row_values(rownum)]
                if only_header:
                    break
        elif file_ext == "csv":
            import csv
            reader = csv.reader(open(self.import_file.path, "rb"))
            for row in reader:
                data += [row]
                if only_header:
                    break
        elif file_ext == "lsx":
            from openpyxl.reader.excel import load_workbook
            wb = load_workbook(filename=self.import_file.path, use_iterators = True)
            sheet = wb.get_active_sheet()
            for row in sheet.iter_rows():
                data_row = []
                for cell in row:
                    data_row += [cell.internal_value]
                data += [data_row]
                if only_header:
                    break
        elif file_ext == "ods":
            from odsreader import ODSReader
            doc = ODSReader(self.import_file.path)
            table = doc.SHEETS.items()[0]

            # Remove blank columns that ods files seems to have
            blank_columns = []
            for i, header_cell in enumerate(table[1][0]):
                if header_cell == "":
                    blank_columns += [i]
            # just an overly complicated way to remove these
            # indexes from a list
            for offset, blank_column in enumerate(blank_columns):
                for row in table[1]:
                    del row[blank_column - offset]

            if only_header:
                data += [table[1][0]]
            else:
                data += table[1]
        if only_header:
            return data[0]
        return data


class RelationalMatch(models.Model):
    """Store which unique field is being use to match.
    This can be used only to set a FK or one M2M relation
    on the import root model. It does not add them.
    With Multple rows set to the same field, you could set more
    than one per row.
    EX Lets say a student has an ID and username and both
    are marked as unique in Django orm. The user could reference
    that student by either."""
    import_log = models.ForeignKey(ImportLog)
    field_name = models.CharField(max_length=255) # Ex student_number_set
    related_field_name = models.CharField(max_length=255, blank=True) # Ex username

    
class ImportedObject(models.Model):
    import_log = models.ForeignKey(ImportLog)
    object_id = models.IntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
