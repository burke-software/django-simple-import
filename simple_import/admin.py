from django.contrib import admin
from simple_import.models import ImportLog, ColumnMatch

class ColumnMatchInline(admin.TabularInline):
    model = ColumnMatch
    extra = 0

class ImportLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'date',)
    #inlines = [ColumnMatchInline]
admin.site.register(ImportLog, ImportLogAdmin)
