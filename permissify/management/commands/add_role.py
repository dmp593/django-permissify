from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from permissify.models import Role


class Command(BaseCommand):
    help = 'Adds a role to the database with preset permissions'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('--permissions', type=str, nargs='*')
        parser.add_argument('--database', type=str, default='default')

    def handle(self, *args, **options):
        role_name = options.get('name')
        perms = options.get('permissions')
        alias = options.get('database')

        role, created = Role.objects.using(alias=alias).get_or_create(name=role_name)

        role.permissions.clear()

        if isinstance(perms, list):
            for perm in perms:
                codename, app_label, model = perm.split(',')

                permission = Permission.objects.using(alias).filter(
                    codename=codename,
                    content_type__app_label=app_label,
                    content_type__model=model
                ).get()

                role.permissions.add(permission)

        role.save()
