from django.contrib import admin

from portal.capstone import models


@admin.register(models.Simulator)
class SimulatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'ends')
    fields = (
        'name',
        'status',
        'endpoint',
        'ends',
        'started',
        'interval',
    )
    readonly_fields = (
        'started',
        'interval',
    )
