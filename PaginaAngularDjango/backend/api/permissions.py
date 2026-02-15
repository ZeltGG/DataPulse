from rest_framework.permissions import BasePermission


def _has_group(user, group_name: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


class IsAdminRole(BasePermission):
    """
    Permite solo usuarios en el grupo ADMIN o superuser.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or _has_group(user, "ADMIN")))


class IsAnalystOrAdmin(BasePermission):
    """
    Permite ANALISTA o ADMIN (o superuser).
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (
                user.is_superuser or _has_group(user, "ADMIN") or _has_group(user, "ANALISTA")
            )
        )


class IsViewerOrAbove(BasePermission):
    """
    Permite VIEWER, ANALISTA o ADMIN (o superuser).
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (
                user.is_superuser
                or _has_group(user, "ADMIN")
                or _has_group(user, "ANALISTA")
                or _has_group(user, "VIEWER")
            )
        )