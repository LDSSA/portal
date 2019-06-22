from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from portal.users.forms import UserChangeForm, UserCreationForm
from portal.users.models import UserWhitelist

User = get_user_model()


@admin.register(UserWhitelist)
class UserWhitelistAdmin(admin.ModelAdmin):
    list_display = ['username', 'student']


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
                    ("User", {"fields": ("name",)}),
                    ("Student", {"fields": ("student", )}),
                    ("Keys", {"fields": ("deploy_private_key",
                                         "deploy_public_key")}),
                ) + auth_admin.UserAdmin.fieldsets
    list_display = ["username", "student", "name", "is_superuser"]
    search_fields = ["name"]
    list_filter = ('student', 'is_superuser', 'is_active', 'groups')
