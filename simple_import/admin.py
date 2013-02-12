from django.contrib import admin
from simple_import.models import ImportLog

class ImportLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'date',)
admin.site.register(ImportLog, ImportLogAdmin)