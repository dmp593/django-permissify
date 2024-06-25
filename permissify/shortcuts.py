import re
from typing import Any, Callable

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from permissify.models import ObjectPermission, Role


User = get_user_model()

_Permission = str | tuple[str, str, str] | Permission
_Permissions = list[_Permission]


def _get_perm(perm: _Permission, obj: Any = None) -> Permission:
    if isinstance(perm, str):
        if '.' in perm:
            app_label, codename = perm.split('.')
            action, model = codename.split('_')
        elif obj is not None:
            ctype = ContentType.objects.get_for_model(obj)
            app_label, model = ctype.app_label, ctype.model

            if perm in ['add', 'change', 'delete', 'view']:
                codename = f'{perm}_{model}'
            else:
                codename = perm

        else:
            raise PermissionError(f'Invalid permission type: {perm}')

        perm = (codename, app_label, model)

    if isinstance(perm, tuple):
        perm = Permission.objects.get_by_natural_key(*perm)

    return perm


def _grant_object_permission(grantee: User | Role | Group, perm: Permission, obj: Model):
    obj_perm, created = ObjectPermission.objects.get_or_create(
        grantee_id=grantee.pk,
        grantee_content_type=ContentType.objects.get_for_model(grantee),
        permission_id=perm.pk,
        object_id=obj.pk,
        object_content_type=ContentType.objects.get_for_model(obj)
    )


def _revoke_object_permission(grantee: User | Role | Group, perm: Permission, obj: Model):
    obj_perm = ObjectPermission.objects.filter(grantee_id=grantee.id, permission=perm, object_id=obj.id)
    obj_perm.delete()


def _perform_grant_or_revoke_perms(
    grantee: User | Role | Group,
    perms: _Permissions,
    fn_grant_or_remove_perm: Callable[[User | Role | Group, str | tuple[str, str, str] | Permission, Model], None],
    obj: Model | None = None
):
    for perm in perms:
        fn_grant_or_remove_perm(grantee, perm, obj)


def _perform_grant_or_revoke_all_perms(
    grantee: User | Role | Group,
    fn: Callable[[User | Role | Group, _Permission | _Permissions, Model], None],
    obj: Model | None = None
):
    ctype = ContentType.objects.get_for_model(obj)
    perms = Permission.objects.filter(content_type=ctype).all()

    _perform_grant_or_revoke_perms(grantee, perms, fn, obj)


def _grant_or_revoke_perms(
    grantee: User | Role | Group,
    perm: _Permission | _Permissions,
    fn_grant_or_revoke: Callable[[User | Role | Group, _Permission | _Permissions, Model | None], None],
    obj: Model | None = None,
) -> bool:
    if isinstance(perm, str):
        # Check for grant/revoke all permissions for an object
        if perm == '__all__' or perm == '*' and obj is not None:
            _perform_grant_or_revoke_all_perms(grantee, fn_grant_or_revoke, obj)
            return True

        # Check for grant/revoke all permissions for an app
        if match := re.match(r"^(?P<app_label>\w+)\.(?:\*|__all__)$", perm):
            app_label = match.group('app_label')
            perm = Permission.objects.filter(content_type__app_label=app_label).all()
            _perform_grant_or_revoke_perms(grantee, perm, fn_grant_or_revoke, obj)

            return True

        # Check for grant/revoke all permissions of a model (including future ones)
        elif match := re.match(r"^(?P<app_label>\w+)\.\*_(?P<model_name>\w+)$", perm):
            app_label, model_name = match.groups()
            ctype = ContentType.objects.get_by_natural_key(app_label, model_name)
            perm = Permission.objects.filter(content_type=ctype).all()
            _perform_grant_or_revoke_perms(grantee, perm, fn_grant_or_revoke, obj)
            return True

        if ',' in perm:
            perm = list(map(str.strip, perm.split(',')))

    if isinstance(perm, list):
        _perform_grant_or_revoke_perms(grantee, perm, fn_grant_or_revoke, obj)
        return True

    return False


def grant_perm(
    grantee: User | Role | Group,
    perm: _Permission | _Permissions,
    obj: Model | None = None
):
    if _grant_or_revoke_perms(grantee, perm, grant_perm, obj):
        return

    perm = _get_perm(perm, obj)

    if obj is not None:
        return _grant_object_permission(grantee, perm, obj)

    permissions_relationship_name = 'user_permissions' if isinstance(grantee, User) else 'permissions'
    permissions_relationship = getattr(grantee, permissions_relationship_name)

    # if not permissions_relationship.filter(pk=perm.pk).exists():
    permissions_relationship.add(perm)


def revoke_perm(
    grantee: User | Role | Group,
    perm: _Permission | _Permissions,
    obj: Model | None = None
):
    if _grant_or_revoke_perms(grantee, perm, revoke_perm, obj):
        return

    perm = _get_perm(perm, obj)

    if obj is not None:
        return _revoke_object_permission(grantee, perm, obj)

    permissions_relationship_name = 'user_permissions' if isinstance(grantee, User) else 'permissions'
    permissions_relationship = getattr(grantee, permissions_relationship_name)

    # if permissions_relationship.filter(pk=perm.pk).exists():
    permissions_relationship.remove(perm)
