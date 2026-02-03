from rest_framework.permissions import BasePermission, SAFE_METHODS


ROLE_ADMIN = "administradores"
ROLE_USUARIO = "usuarios"
ROLE_CONSULTOR = "consultores"


def user_in_group(user, role_name: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True if role_name == ROLE_ADMIN else False
    return user.groups.filter(name=role_name).exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return user_in_group(request.user, ROLE_ADMIN)


class IsUsuario(BasePermission):
    def has_permission(self, request, view):
        return user_in_group(request.user, ROLE_USUARIO)


class IsConsultor(BasePermission):
    def has_permission(self, request, view):
        return user_in_group(request.user, ROLE_CONSULTOR)


class MedicationAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return (
                user_in_group(request.user, ROLE_ADMIN)
                or user_in_group(request.user, ROLE_USUARIO)
                or user_in_group(request.user, ROLE_CONSULTOR)
            )
        return user_in_group(request.user, ROLE_ADMIN) or user_in_group(
            request.user, ROLE_USUARIO
        )
