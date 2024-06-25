import argparse

from django.core.management.base import BaseCommand

from permissify.models import Role


class Command(BaseCommand):
    help = 'Removes a Role from the database and clears all permissions associated with it.'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('--database', type=str, default='default')

    def handle(self, *args, **options):
        role_name = options.get('name')
        alias = options.get('database')

        Role.objects.using(alias=alias).filter(name=role_name).delete()
