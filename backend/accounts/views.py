import time

from django.contrib.auth.models import User
from django.db.utils import OperationalError
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.permissions import IsAdmin
from accounts.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "first_name", "last_name"]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

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

# Create your views here.
