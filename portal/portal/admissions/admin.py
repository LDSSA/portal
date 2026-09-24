from constance.admin import Config, ConstanceAdmin
from django.contrib import admin

from .forms import AdmissionsConfigForm


class AdmissionsConstanceAdmin(ConstanceAdmin):
    change_list_form = AdmissionsConfigForm


admin.site.unregister([Config])
admin.site.register([Config], AdmissionsConstanceAdmin)
