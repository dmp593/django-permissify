from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import models as auth_models
from django.contrib.auth.models import _user_get_permissions
from django.db import models
from django.utils.translation import gettext_lazy as _

from permissify import managers


class Role(models.Model):
    name = models.CharField(_("name"), max_length=150, unique=True)
    permissions = models.ManyToManyField(
        auth_models.Permission,
        verbose_name=_("permissions"),
        blank=True,
    )

    objects = managers.RoleManager()

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")

    def __str__(self):
        return str(self.name)

    def natural_key(self):
        return (self.name,)


class RolePermissionsMixin(auth_models.PermissionsMixin):
    """
    Add the fields and methods necessary to support the Group and Permission
    models using the ModelBackend.
    """

    roles = models.ManyToManyField(
        Role,
        verbose_name=_("roles"),
        blank=True,
        help_text=_(
            "The roles this user belongs to. A user will get all permissions "
            "granted to each of their roles."
        ),
        related_name="user_set",
        related_query_name="user",
    )

    class Meta:
        abstract = True

    def get_role_permissions(self, obj=None):
        """
        Return a list of permission strings that this user has through their
        roles. Query all available auth backends. If an object is passed in,
        return only permissions matching this object.
        """
        return _user_get_permissions(self, obj, "role")


class User(RolePermissionsMixin, auth_models.AbstractUser):
    class Meta(auth_models.AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'


class ObjectPermission(models.Model):
    grantee_content_type = models.ForeignKey(
        to=ContentType,
        limit_choices_to=models.Q(
            app_label__in=['auth', 'users'],
            model__in=['user', 'group', 'role']
        ),
        related_name="granted_object_permission_set",
        related_query_name="granted_object_permission",
        on_delete=models.CASCADE,
    )

    grantee_id = models.CharField(
        db_index=True,
        max_length=150
    )

    object_content_type = models.ForeignKey(
        to=ContentType,
        related_name="object_permission_set",
        related_query_name="object_permission",
        editable=False,
        on_delete=models.CASCADE,
    )

    object_id = models.CharField(
        db_index=True,
        max_length=150
    )

    # Whom to grant (User, Role or Group)
    grantee = GenericForeignKey(
        "grantee_content_type",
        "grantee_id"
    )

    # Which object do you want to grant permission
    object = GenericForeignKey(
        "object_content_type",
        "object_id",
    )

    # What Permission you want to give
    permission = models.ForeignKey(
        to=auth_models.Permission,
        on_delete=models.CASCADE
    )

    # Is it to the entire object ('__all__') or to a specific property?
    # property = models.CharField(max_length=150, null=False, default="__all__")

    class Meta:
        unique_together = (
            (
                "grantee_content_type",
                "grantee_id",
                "object_content_type",
                "object_id",
                "permission",
            ),
        )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.object_content_type is None:
            self.object_content_type = self.permission.content_type

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f"{self.permission}({self.object_id}) | {self.grantee}({self.grantee_id})"
