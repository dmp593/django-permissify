from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from permissify import models
from permissify.utils import model_field_exists


UserModel = get_user_model()


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "permissions":
            qs = kwargs.get("queryset", db_field.remote_field.model.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs["queryset"] = qs.select_related("content_type")
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)


if model_field_exists(UserModel, 'roles'):
    # Extending Django's default UserAdmin to include the roles field
    permissions_fields = list(UserAdmin.fieldsets[2][1]['fields'])
    permissions_fields.insert(-2, "roles")

    UserAdmin.list_filter = ("is_staff", "is_superuser", "is_active", "roles", "groups")
    UserAdmin.filter_horizontal = ("roles", "groups", "user_permissions",)
    UserAdmin.fieldsets[2][1]['fields'] = tuple(permissions_fields)

    admin.site.register(UserModel, UserAdmin)

admin.site.register(models.ObjectPermission)
