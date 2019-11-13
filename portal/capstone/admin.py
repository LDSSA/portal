from django.contrib import admin

from portal.capstone import models


@admin.register(models.Capstone)
class CapstoneAdmin(admin.ModelAdmin):
    list_display = ('name', )
    fields = ('name', )


@admin.register(models.StudentApp)
class StudentAppAdmin(admin.ModelAdmin):
    list_display = ('capstone', 'student', 'app_name')
    fields = ('capstone', 'student', 'app_name')


@admin.register(models.Simulator)
class SimulatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'capstone', 'status', 'ends')
    fields = (
        'name',
        'capstone',
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


@admin.register(models.Datapoint)
class DatapointAdmin(admin.ModelAdmin):
    list_display = ('id', 'simulator', 'data')
    fields = ('simulator', 'data')


@admin.register(models.DueDatapoint)
class DueDatapointAdmin(admin.ModelAdmin):
    list_display = ('id', 'simulator', 'student', 'datapoint', 'due')
    fields = (
        'simulator',
        'student',
        'datapoint',
        'status',
        'due',
        'url',
        'response_content',
        'response_exception',
        'response_traceback',
        'response_elapsed',
        'response_status',
        'response_timeout',
    )
    readonly_fields = (
        'simulator',
        'student',
        'datapoint',
        'due',
        'url',
        'response_content',
        'response_exception',
        'response_traceback',
        'response_elapsed',
        'response_status',
        'response_timeout',
    )
