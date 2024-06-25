from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model


def model_field_exists(cls: Model, field: str):
    try:
        cls._meta.get_field(field)
        return True
    except FieldDoesNotExist:
        return False
