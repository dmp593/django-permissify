from django.test import TestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from permissify.models import Role
from permissify.shortcuts import grant_perm, revoke_perm


User = get_user_model()


class ObjectPermissionThroughRoleTestCase(TestCase):
    def test_grant_user_obj_perm_through_role(self):
        user = User.objects.create_user(username='test', password='test', email='test@test.test')
        role = Role.objects.create(name='role')

        user.roles.add(role)

        group1 = Group.objects.create(name='group1')
        group2 = Group.objects.create(name='group2')

        grant_perm(role, 'auth.change_group', group1)
        user = User.objects.get(pk=user.pk)

        self.assertTrue(
            user.has_perm('auth.change_group', group1)
        )

        self.assertFalse(
            user.has_perm('auth.change_group', group2)
        )

        self.assertFalse(
            user.has_perm('auth.change_group')
        )

    def test_revoke_user_obj_perm_through_role(self):
        user = User.objects.create_user(username='test', password='test', email='test@test.test')
        role = Role.objects.create(name='role')

        user.roles.add(role)

        group1 = Group.objects.create(name='group1')
        group2 = Group.objects.create(name='group2')

        grant_perm(role, 'auth.change_group', group1)
        user = User.objects.get(pk=user.pk)

        self.assertTrue(
            user.has_perm('auth.change_group', group1)
        )

        self.assertFalse(
            user.has_perm('auth.change_group', group2)
        )

        self.assertFalse(
            user.has_perm('auth.change_group')
        )

        revoke_perm(role, 'auth.change_group', group1)
        user = User.objects.get(pk=user.pk)

        self.assertFalse(
            user.has_perm('auth.change_group', group1)
        )

        self.assertFalse(
            user.has_perm('auth.change_group', group2)
        )

        self.assertFalse(
            user.has_perm('auth.change_group')
        )
