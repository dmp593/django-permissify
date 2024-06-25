from django.test import TestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from permissify.models import Role
from permissify.shortcuts import grant_perm, revoke_perm


User = get_user_model()


class ObjectPermissionThroughGroupTestCase(TestCase):
    def test_grant_user_obj_perm_through_group(self):
        user = User.objects.create_user(username='test', password='test', email='test@test.test')
        group = Group.objects.create(name='group')

        user.groups.add(group)

        role1 = Role.objects.create(name='role1')
        role2 = Role.objects.create(name='role2')

        grant_perm(group, 'permissify.change_role', role1)
        user = User.objects.get(pk=user.pk)

        self.assertTrue(
            user.has_perm('permissify.change_role', role1)
        )

        self.assertFalse(
            user.has_perm('permissify.change_role', role2)
        )

        self.assertFalse(
            user.has_perm('permissify.change_role')
        )

    def test_revoke_user_obj_perm_through_group(self):
        user = User.objects.create_user(username='test', password='test', email='test@test.test')
        group = Group.objects.create(name='group')

        user.groups.add(group)

        role1 = Role.objects.create(name='role1')
        role2 = Role.objects.create(name='role2')

        grant_perm(group, 'permissify.change_role', role1)
        user = User.objects.get(pk=user.pk)

        self.assertTrue(
            user.has_perm('permissify.change_role', role1)
        )

        self.assertFalse(
            user.has_perm('permissify.change_role', role2)
        )

        self.assertFalse(
            user.has_perm('permissify.change_role')
        )

        revoke_perm(group, 'permissify.change_role', role1)
        user = User.objects.get(pk=user.pk)

        self.assertFalse(
            user.has_perm('permissify.change_role', role1)
        )

        self.assertFalse(
            user.has_perm('permissify.change_role', role2)
        )

        self.assertFalse(
            user.has_perm('permissify.change_role')
        )
