from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from rest_framework.test import APITestCase
from rest_framework import status


User = get_user_model()


class DRFPermissionsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.group = Group.objects.create(name='testgroup')
        self.user.groups.add(self.group)
        self.permission = Permission.objects.get(codename='add_user')
        self.group.permissions.add(self.permission)

    def test_permissify_object_permissions(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/mock-view/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permissify_object_permissions_or_anon_read_only(self):
        # Test anonymous read-only access
        response = self.client.get('/mock-view-anon-read-only/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test authenticated write access
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/mock-view-anon-read-only/', {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test anonymous write access (should be forbidden)
        self.client.logout()
        response = self.client.post('/mock-view-anon-read-only/', {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
