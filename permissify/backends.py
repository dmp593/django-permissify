from django.contrib.auth import backends, models, get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Permission
from django.db.models import OuterRef, Q, Exists

from permissify.utils import model_field_exists
from permissify.models import User, ObjectPermission


UserModel = get_user_model()


class PermissionModelBackend(backends.ModelBackend):

    @property
    def _user_model_has_field_roles(self):
        return model_field_exists(UserModel, 'roles')

    def _get_role_permissions(self, user_obj: User):
        if not self._user_model_has_field_roles:
            return models.Permission.objects.none()

        user_roles_field = UserModel._meta.get_field("roles")
        user_roles_query = "role__%s" % user_roles_field.related_query_name()

        return models.Permission.objects.filter(**{user_roles_query: user_obj})

    def get_role_permissions(self, user_obj, obj=None) -> set:
        return self._get_permissions(user_obj, obj, from_name="role")

    def _get_all_permissions(self, user_obj, obj=None, perm_cache_key="_perm_cache") -> set:
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()

        if not hasattr(user_obj, perm_cache_key):
            setattr(
                user_obj,
                perm_cache_key,
                {
                    *BaseBackend.get_all_permissions(self, user_obj=user_obj, obj=obj),
                    *self.get_role_permissions(user_obj, obj=obj)
                }
            )

        return getattr(user_obj, perm_cache_key)

    def get_all_permissions(self, user_obj, obj=None) -> set:
        if obj is not None:
            return set()

        return self._get_all_permissions(user_obj, obj)

    def with_perm(self, perm, is_active=True, include_superusers=True, obj=None):
        """
        Return users that have permission "perm". By default, filter out
        inactive users and include superusers.
        """
        if isinstance(perm, str):
            try:
                app_label, codename = perm.split(".")
            except ValueError:
                raise ValueError(
                    "Permission name should be in the form "
                    "app_label.permission_codename."
                )
        elif not isinstance(perm, Permission):
            raise TypeError(
                "The `perm` argument must be a string or a permission instance."
            )

        if obj is not None:
            return UserModel._default_manager.none()

        permission_q = Q(group__user=OuterRef("pk")) | Q(user=OuterRef("pk"))

        if self._user_model_has_field_roles:
            permission_q |= Q(role__user=OuterRef("pk"))

        if isinstance(perm, Permission):
            permission_q &= Q(pk=perm.pk)
        else:
            permission_q &= Q(codename=codename, content_type__app_label=app_label)

        user_q = Exists(Permission.objects.filter(permission_q))
        if include_superusers:
            user_q |= Q(is_superuser=True)
        if is_active is not None:
            user_q &= Q(is_active=is_active)

        return UserModel._default_manager.filter(user_q)


class ObjectPermissionModelBackend(PermissionModelBackend):

    def get_all_permissions(self, user_obj, obj=None) -> set:
        if obj is None:
            return super().get_all_permissions(user_obj, obj)

        return self._get_all_permissions(user_obj, obj, perm_cache_key=f"_obj_perm_cache_{obj.pk}")

    def get_user_permissions(self, user_obj, obj=None):
        return self._get_permissions(user_obj, obj, "user_obj" if obj is not None else "user")

    def get_group_permissions(self, user_obj, obj=None):
        return self._get_permissions(user_obj, obj, "group_obj" if obj is not None else "group")

    def get_role_permissions(self, user_obj, obj=None) -> set:
        return self._get_permissions(user_obj, obj, from_name="role_obj" if obj is not None else "role")

    def _get_user_obj_permissions(self, user_obj, obj=None):
        user_perms = self._get_user_permissions(user_obj)

        if obj is None:
            return user_perms

        return user_perms | Permission.objects.filter(
            Exists(
                ObjectPermission.objects.filter(
                    permission=OuterRef("pk"),
                    object_id=obj.pk,
                    grantee_id=user_obj.pk,
                )
            )
        )

    def _get_group_obj_permissions(self, user_obj, obj=None):
        group_perms = self._get_group_permissions(user_obj)

        if obj is None:
            return group_perms

        return group_perms | Permission.objects.filter(
            Exists(
                ObjectPermission.objects.filter(
                    permission=OuterRef("pk"),
                    object_id=obj.pk,
                    grantee_id__in=user_obj.groups.all().values_list("id", flat=True),
                )
            )
        )

    def _get_role_obj_permissions(self, user_obj, obj=None):
        if not self._user_model_has_field_roles:
            return Permission.objects.none()

        role_perms = self._get_role_permissions(user_obj)

        if obj is None:
            return role_perms

        return role_perms | Permission.objects.filter(
            Exists(
                ObjectPermission.objects.filter(
                    permission=OuterRef("pk"),
                    object_id=obj.pk,
                    grantee_id__in=user_obj.roles.all().values_list("id", flat=True),
                )
            )
        )

    def _get_permissions(self, user_obj, obj, from_name):
        """
        Return the permissions of `user_obj` from `from_name`. `from_name` can
        be either "group", "user", "role", "group_obj", "user_obj", or "role_obj"
        to return permissions from:
            `_get_group_permissions`,
            `_get_user_permissions`,
            `_get_role_permissions`,
            `_get_group_obj_permissions`,
            `_get_user_obj_permissions`,
            `_get_role_obj_permissions`,
            respectively.
        """

        if not user_obj.is_active or user_obj.is_anonymous:
            return set()

        if obj is None:
            return super()._get_permissions(user_obj, obj, from_name)

        perm_cache_name = f"_{from_name}_perm_cache_{obj.pk}"
        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                perms = getattr(self, "_get_%s_permissions" % from_name)(user_obj, obj)
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(
                user_obj, perm_cache_name, {"%s.%s" % (ct, name) for ct, name in perms}
            )
        return getattr(user_obj, perm_cache_name)

    def has_perm(self, user_obj, perm, obj=None):
        if user_obj.is_superuser:
            return True

        return super().has_perm(user_obj, perm, obj)

    def with_perm(self, perm, is_active=True, include_superusers=True, obj=None):
        """
        Return users that have permission "perm". By default, filter out
        inactive users and include superusers.
        """
        if obj is None:
            return super().with_perm(perm, is_active, include_superusers, obj)
        
        if isinstance(perm, str):
            try:
                app_label, codename = perm.split(".")
            except ValueError:
                raise ValueError(
                    "Permission name should be in the form "
                    "app_label.permission_codename."
                )
        elif not isinstance(perm, (ObjectPermission, Permission)):
            raise TypeError(
                "The `perm` argument must be a string or an object permission instance."
            )

        permission_q = Q(permission__group__user=OuterRef("pk")) | Q(permission__user=OuterRef("pk"))

        if self._user_model_has_field_roles:
            permission_q |= Q(permission__role__user=OuterRef("pk"))

        if isinstance(perm, ObjectPermission):
            permission_q &= Q(pk=perm.permission.pk, )

        elif isinstance(perm, Permission):
            permission_q &= Q(pk=perm.pk)

        else:
            permission_q &= Q(permission__codename=codename, permission__content_type__app_label=app_label)

        user_q = Exists(ObjectPermission.objects.filter(permission_q, object_id=obj.pk))

        if include_superusers:
            user_q |= Q(is_superuser=True)

        if is_active is not None:
            user_q &= Q(is_active=is_active)

        return UserModel._default_manager.filter(user_q)
