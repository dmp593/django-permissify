# Django Permissify

Django Permissify is a reusable Django app that provides a robust and flexible way to manage object-level permissions. It allows you to assign permissions to users and groups on a per-object basis, enhancing the default Django permissions system.

## Features

- Assign permissions to users and groups on a per-object basis.
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

## Configuration

### Settings

- (Optional) **AUTH_USER_MODEL**: Set this to `'permissify.User'` if you want to use the custom model provided by the app, which includes Roles.

    ```python
    AUTH_USER_MODEL = 'permissify.User'
    ```

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

# You can instead pass the permission instance
perm = Permission.objects.get(pk=<...>)
grant_perm(user, perm)
# or for object permission only: grant_perm(user, perm, obj)

# Grant all permissions to an obj
grant_perm(user, '*', obj)
grant_perm(user, '__all__', obj)

# Grant all permissions of an app
grant_perm(user, '<app_label>.*')  # grants all permissions of an app
grant_perm(user, '<app_label>.__all__')

# Grant all permissions of a model (including future ones)
grant_perm(user, '<app_label>.*_<model_name>')
# or: grant_perm(user, '<app_label>.*_<model_name>', obj) for a object-level permission

```

#### Revoking a Permission

```python
from permissify.shortcuts import revoke_perm
from django.contrib.auth.models import Permission

# Revoke a permission from a user
revoke_perm(user, '<app_label>.<permission>_<model_name>')

# Revoke a permission from a user for a specific object
revoke_perm(user, '<app_label>.<permission>_<model_name>', obj)

# You can instead pass the permission instance
perm = Permission.objects.get(pk=<...>)
revoke_perm(user, perm)  # or for object permission only: revoke_perm(user, perm, obj)

# Revoke all permissions of an obj
revoke_perm(user, '*', obj)
revoke_perm(user, '__all__', obj)

# Revoke all permissions of an app
revoke_perm(user, '<app_label>.*')  # revokes all permissions of an app
revoke_perm(user, '<app_label>.__all__')

# Revoke all permissions of a model (including future ones)
revoke_perm(user, '<app_label>.*_<model_name>')
# or: revoke_perm(user, '<app_label>.*_<model_name>', obj) for a object-level permission

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

#### Why Use a Role Model Instead of Just the Group Model if they are identical tables?
Separate Logical Concerns of Groups vs Roles:

Groups: Typically used to manage permissions for a collection of users who share common access needs. For example, a "Editors" group might have permissions to edit articles.
Roles: Often represent a user's position or function within an organization, such as "Manager" or "Employee". Roles can be used to encapsulate a set of permissions that are tied to a specific job function.
Additional Model for Other Types of Permissions:

Having a separate Role model allows for more granular control over permissions. For instance, in a subscription-based application, roles can be used to determine if a user has paid for a subscription, while groups can be used to manage specific permissions within the application.
Business Enterprises Preference:

Many enterprises prefer the concept of roles because it aligns more closely with organizational structures. Roles can be used to define job functions and responsibilities, making it easier to manage permissions based on an employee's role within the company.
Flexibility and Extensibility:

Using a separate Role model provides flexibility to extend the model with additional fields and methods that are specific to roles. This can include custom logic for role-based access control, additional metadata, or integration with other systems.