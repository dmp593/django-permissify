from django.db import models
from django.contrib.auth.models import UserManager  # noqa: F401


class RoleManager(models.Manager):
    """
    The manager for the Role model.
    """

    use_in_migrations = True

    def get_by_natural_key(self, name):
        return self.get(name=name)
