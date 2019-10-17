from django.contrib import admin

from .models import Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    readonly_fields = ('obj', 'src', 'revision', 'created', 'updated')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'created',)},),
        ('Change info', {'fields': ('publisher', 'version', 'author', 'revision', 'updated',)},),
    )
    list_display = ('name', 'revision', 'author', 'version', 'publisher')
