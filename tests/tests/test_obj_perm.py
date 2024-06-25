from django.test import TestCase

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from permissify.shortcuts import grant_perm, revoke_perm


User = get_user_model()


class UserObjectPermissionTestCase(TestCase):
    def test_grant_user_obj_perm(self):
        user = User.objects.create_user(username='test', password='test', email='test@test.test')

        group1 = Group.objects.create(name='group1')
        group2 = Group.objects.create(name='group2')

        grant_perm(user, 'auth.change_group', group1)
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

    def test_revoke_user_obj_perm(self):
        user = User.objects.create_user(username='test', password='test', email='test@test.test')

        group1 = Group.objects.create(name='group1')
        group2 = Group.objects.create(name='group2')

        grant_perm(user, 'auth.change_group', group1)
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

        revoke_perm(user, 'auth.change_group', group1)
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
