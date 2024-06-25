# Django Permissify

Django Permissify is a reusable Django app that provides a robust and flexible way to manage object-level permissions. It allows you to assign permissions to users and groups on a per-object basis, enhancing the default Django permissions system.

## Features

- Assign permissions to users, groups (and optionally roles) on a per-object basis.
- Manage roles and permissions through Django admin.
- Integrates seamlessly with Django's authentication system.
- Provides management commands for adding and removing roles.

## Installation

1. Install the package using pip:

    ```bash
    pip install django-permissify
    ```

2. Add `permissify` to your `INSTALLED_APPS` in your Django settings:

    ```python
    INSTALLED_APPS = [
        ...
        'permissify',
    ]
    ```

3. Add the custom authentication backend to your `AUTHENTICATION_BACKENDS`:

    ```python
    AUTHENTICATION_BACKENDS = [
        'permissify.backends.ObjectPermissionModelBackend',
        ...
    ]
    ```

4. Run the migrations to create the necessary database tables:

    ```bash
    python manage.py migrate
    ```

## Optional Configurations

- If you want to use the custom User model provided by this app, which includes roles, set the **AUTH_USER_MODEL** in your `settings.py` to `permissify.User`:

    ```python
    AUTH_USER_MODEL = 'permissify.User'
    ```

Please refer to [Django's documentation](https://docs.djangoproject.com/en/5.0/topics/auth/customizing/#changing-to-a-custom-user-model-mid-project) to determine if this change is suitable for your project.

## Usage

### Granting and Revoking Permissions

#### Granting a Permission

```python
from permissify.shortcuts import grant_perm
from django.contrib.auth.models import Permission

# Grant a permission to a user
grant_perm(user, '<app_label>.<permission>_<model_name>')

# Grant a permission to a user for a specific object
grant_perm(user, '<app_label>.<permission>_<model_name>', obj)

# Pass the permission instance directly
perm = Permission.objects.get(pk=<...>)
grant_perm(user, perm)
# or for object permission only: grant_perm(user, perm, obj)

# Grant all permissions to an object
grant_perm(user, '*', obj)
grant_perm(user, '__all__', obj)

# Grant all permissions of an app
grant_perm(user, '<app_label>.*')
grant_perm(user, '<app_label>.__all__')

# Grant all permissions of a model (including future ones)
grant_perm(user, '<app_label>.*_<model_name>')
# or: grant_perm(user, '<app_label>.*_<model_name>', obj) for an object-level permission
```

#### Revoking a Permission

```python
from permissify.shortcuts import revoke_perm
from django.contrib.auth.models import Permission

# Revoke a permission from a user
revoke_perm(user, '<app_label>.<permission>_<model_name>')

# Revoke a permission from a user for a specific object
revoke_perm(user, '<app_label>.<permission>_<model_name>', obj)

# Pass the permission instance directly
perm = Permission.objects.get(pk=<...>)
revoke_perm(user, perm)  # or for object permission only: revoke_perm(user, perm, obj)

# Revoke all permissions of an object
revoke_perm(user, '*', obj)
revoke_perm(user, '__all__', obj)

# Revoke all permissions of an app
revoke_perm(user, '<app_label>.*')
revoke_perm(user, '<app_label>.__all__')

# Revoke all permissions of a model (including future ones)
revoke_perm(user, '<app_label>.*_<model_name>')
# or: revoke_perm(user, '<app_label>.*_<model_name>', obj) for an object-level permission
```

#### Granting or Revoking Permissions Through a Group or Role

The same logic for granting or revoking permissions can be applied to groups or roles. Use the default Django method to check permissions with `user.has_perm(...)`.

##### Granting / Revoking Through a Group

```python
from permissify.shortcuts import grant_perm, revoke_perm
from django.contrib.auth import get_user_model
from permissify.models import Group

User = get_user_model()

foo = User.objects.create_user(username="foo", email="foo@example.com", password="foo")
bar = User.objects.create_user(username="bar", email="bar@example.com", password="bar")

group = Group.objects.create(name="pro-membership")

foo.groups.add(group)

grant_perm(group, "<app_label>.<permission>_<model_name>")

# Refer to Django documentation to understand why you need to refresh the user instance
# after granting or revoking a permission:
# https://docs.djangoproject.com/en/5.0/topics/auth/default/#permission-caching
foo = User.objects.get(pk=foo.pk)

assert foo.has_perm("<app_label>.<permission>_<model_name>")

# Some code logic ...

revoke_perm(group, "<app_label>.<permission>_<model_name>")
foo = User.objects.get(pk=foo.pk)

assert not foo.has_perm("<app_label>.<permission>_<model_name>")
```

##### Granting / Revoking Through a Role

If you swapped your authentication model to use `permissify.User`, you can also manage roles.

```python
from permissify.shortcuts import grant_perm, revoke_perm
from django.contrib.auth import get_user_model
from permissify.models import Role

User = get_user_model()

foo = User.objects.create_user(username="foo", email="foo@example.com", password="foo")
bar = User.objects.create_user(username="bar", email="bar@example.com", password="bar")

role = Role.objects.create(name="editor")

foo.roles.add(role)

grant_perm(role, "<app_label>.<permission>_<model_name>")

# Refresh the user instance after granting or revoking a permission:
# https://docs.djangoproject.com/en/5.0/topics/auth/default/#permission-caching
foo = User.objects.get(pk=foo.pk)

assert foo.has_perm("<app_label>.<permission>_<model_name>")

# Some code logic ...

revoke_perm(role, "<app_label>.<permission>_<model_name>")
foo = User.objects.get(pk=foo.pk)

assert not foo.has_perm("<app_label>.<permission>_<model_name>")
```

###### NOTE

If you cannot swap your model to `permissify.User` but still want to include roles in your project, you can add the `RolePermissionMixin` to your user model.

Ensure that you don't already have a "roles" field in your User model, as this will be used for the `ManyToManyField` relationship to the `Role` model.

For example:

```python
# foo/models.py

from django.contrib.auth import models as auth_models

class FooUser(ExternalAppUser, ComplexStuffUser, auth_models.AbstractUser):
    # some stuff...
    ...

# settings.py
AUTH_USER_MODEL = 'foo.FooUser'
```

To include roles without swapping, update your current model to include `RolePermissionMixin` and run migrations to include relationships to roles.

```python
# foo/models.py

from django.contrib.auth import models as auth_models
from permissify.models import RolePermissionMixin

# Pay close attention to the order of inheritance
class FooUser(ExternalAppUser, ComplexStuffUser, RolePermissionMixin, auth_models.AbstractUser):
    # some stuff...
    ...
```

### Management Commands

#### Adding a Role

```bash
python manage.py add_role <role_name> --permissions [<app_label.permission_codename>, ...]
```

### Removing a Role

```bash
python manage.py remove_role <role_name>
```

#### Why Use a Role Model Instead of Just the Group Model if They Are Identical Tables?

##### Separate Logical Concerns of Groups vs Roles

**Groups:** Typically used to manage permissions for users with common access needs. For example, an "editors" group might have permission to edit articles. A "users" group can comment on the editors' posts. A "Moderator" role, for example, can validate both posts and comments, crossing both groups. Instead of a "moderators" group, it's more semantically correct to have a "Moderator" role that can validate editors' posts and users' comments.

**Roles:** Often represent a user's position or function within an organization, such as "Manager" or "Employee". Roles encapsulate a set of permissions tied to a specific job function.

##### Additional Model for Other Types of Permissions

Having a separate Role model allows for more granular control over permissions. For instance, in a subscription-based application, groups can determine if a user has paid for a subscription (e.g., a group of "pro" users), while roles manage specific permissions within the application (e.g., editor, contributor, moderator).

##### Business Enterprises Preference

Many enterprises prefer the concept of roles because it aligns more closely with organizational structures. Roles define job functions and responsibilities, making it easier to manage permissions based on an employee's role within the company.

##### Flexibility and Extensibility

Using a separate Role model provides flexibility to extend the model with additional fields and methods specific to roles. This includes custom logic for role-based access control, additional metadata, or integration with other systems.

---

Thank you for reading!

If you like this library, you can support me by [buying me a coffee](https://www.buymeacoffee.com/dmp593).