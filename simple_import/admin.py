from django.contrib import admin
from simple_import.models import ImportLog, ColumnMatch

class ImportLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'date',)
    def has_add_permission(self, request):
        return False
admin.site.register(ImportLog, ImportLogAdmin)
