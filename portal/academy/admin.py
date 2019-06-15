from django.contrib import admin
from portal.academy import models


@admin.register(models.Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')


@admin.register(models.Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        'get_code',
        'name',
        'instructor',
        'due_date',
        'open',
    )
    fields = (
        'open',
        'specialization',
        'code',
        'name',
        'description',
        'instructor',
        'checksum',
    )

    def get_code(self, obj):
        return str(obj)
    get_code.short_description = 'Code'


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        'unit',
        'student',
        'status',
        'score',
    )
