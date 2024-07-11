from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from permissify.drf.permissions import PermissifyObjectPermissions, PermissifyObjectPermissionsOrAnonReadOnly
from tests.serializers import UserSerializer


User = get_user_model()


class MockViewSet(viewsets.ModelViewSet):
    permission_classes = [PermissifyObjectPermissions]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        return Response({'detail': 'success'}, status=status.HTTP_200_OK)


class MockViewAnonReadOnlySet(viewsets.ModelViewSet):
    permission_classes = [PermissifyObjectPermissionsOrAnonReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        return Response({'detail': 'success'}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        return Response({'detail': 'success'}, status=status.HTTP_201_CREATED)
