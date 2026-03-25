import time
from urllib.parse import quote

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.utils import OperationalError
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.permissions import IsAdmin
from accounts.serializers import UserSerializer


class SISASTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        try:
            data["must_change_password"] = bool(self.user.profile.must_change_password)
        except Exception:
            data["must_change_password"] = False
        return data


class SISASTokenObtainPairView(TokenObtainPairView):
    serializer_class = SISASTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "first_name", "last_name"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = list(serializer.data)
        return Response(
            {
                "count": len(data),
                "next": None,
                "previous": None,
                "results": data,
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin], url_path="credential-email")
    def credential_email(self, request, pk=None):
        target_user = self.get_object()
        admin_email = (request.user.email or "").strip()
        target_email = (target_user.email or "").strip()

        if not admin_email:
            return Response(
                {"detail": "El administrador en sesion no tiene correo configurado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not target_email:
            return Response(
                {"detail": "El usuario no tiene correo configurado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = target_user.profile
        except Exception:
            profile = None

        temporary_password = (profile.temporary_password or "").strip() if profile else ""
        must_change_password = bool(profile and profile.must_change_password)

        if not must_change_password or not temporary_password or not temporary_password[0].isdigit():
            return Response(
                {
                    "detail": (
                        "El usuario no tiene una contrasena temporal lista para enviar. "
                        "Solo aplica a contrasenas que empiezan con numero."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject = "Credenciales SISAS"
        body = (
            "Su usuario y contrasena para el sistema SISAS es:\n"
            f"Usuario: {target_user.username}\n"
            f"Contrasena temporal: {temporary_password}\n\n"
            "Al iniciar sesion debera cambiar su contrasena."
        )
        query_string = "&".join(
            [
                f"cc={quote(admin_email)}",
                f"subject={quote(subject)}",
                f"body={quote(body)}",
            ]
        )
        return Response(
            {
                "mailto_url": f"mailto:{target_email}?{query_string}",
                "detail": "Correo listo para abrir en el cliente del administrador.",
            }
        )

    def create(self, request, *args, **kwargs):
        return self._with_retry(lambda: super(UserViewSet, self).create(request, *args, **kwargs))

    def update(self, request, *args, **kwargs):
        return self._with_retry(lambda: super(UserViewSet, self).update(request, *args, **kwargs))

    def partial_update(self, request, *args, **kwargs):
        return self._with_retry(lambda: super(UserViewSet, self).partial_update(request, *args, **kwargs))

    def destroy(self, request, *args, **kwargs):
        return self._with_retry(lambda: super(UserViewSet, self).destroy(request, *args, **kwargs))

    def _with_retry(self, fn, retries=5, base_delay=0.1):
        for attempt in range(retries):
            try:
                return fn()
            except OperationalError as exc:
                if "database is locked" not in str(exc).lower():
                    raise
                time.sleep(base_delay * (attempt + 1))
        return Response(
            {"detail": "Base de datos ocupada. Intenta de nuevo."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            return Response({"detail": "Token invalido."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangeOwnPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = str(request.data.get("current_password", ""))
        new_password = str(request.data.get("new_password", ""))

        if not current_password or not new_password:
            return Response(
                {"detail": "current_password y new_password son requeridos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(current_password):
            return Response(
                {"detail": "La contrasena actual es incorrecta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=request.user)
        except DjangoValidationError as exc:
            return Response(
                {"detail": " ".join(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])

        profile = getattr(request.user, "profile", None)
        if profile:
            profile.must_change_password = False
            profile.temporary_password = ""
            profile.save(update_fields=["must_change_password", "temporary_password"])

        return Response({"detail": "Contrasena actualizada correctamente."})

# Create your views here.
