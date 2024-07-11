from rest_framework.permissions import DjangoObjectPermissions, SAFE_METHODS


class PermissifyObjectPermissions(DjangoObjectPermissions):
    def has_permission(self, request, view):
        # For list or other non-object-specific actions, check model-level permissions
        if not view.detail:
            return super().has_permission(request, view)

        # For detail views, bypass and delegate to has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        # For detail actions, check object-level permissions
        if super().has_object_permission(request, view, obj):
            return True

        # Fallback to model-level permissions if object-level permission fails
        return super().has_permission(request, view)


class PermissifyObjectPermissionsOrAnonReadOnly(PermissifyObjectPermissions):
    def has_permission(self, request, view):
        if request.user.is_anonymous and request.method in SAFE_METHODS:
            return True

        return super().has_permission(request, view)
