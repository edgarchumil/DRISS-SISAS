import io
import os
import zipfile

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsAdmin


class BackupDownloadView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        db_path = settings.DATABASES.get("default", {}).get("NAME")
        if not db_path or not os.path.exists(db_path):
            return HttpResponse("Base de datos no encontrada.", status=404)

        password = str(request.data.get("password", "")).strip()
        if not password or not request.user.check_password(password):
            return HttpResponse("Contrasena incorrecta.", status=403)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(db_path, arcname=os.path.basename(db_path))

        buffer.seek(0)
        timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="backup_{timestamp}.zip"'
        return response
