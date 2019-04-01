from django.contrib import admin
from portal.academy import models


@admin.register(models.Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Unit)
class UnitAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    pass
