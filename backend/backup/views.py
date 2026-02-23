import io
import os
import subprocess
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
        password = str(request.data.get("password", "")).strip()
        if not password or not request.user.check_password(password):
            return HttpResponse("Contrasena incorrecta.", status=403)

        db_config = settings.DATABASES.get("default", {})
        engine = db_config.get("ENGINE", "")
        if "postgresql" not in engine:
            return HttpResponse("Respaldo soportado solo para PostgreSQL.", status=400)

        db_name = db_config.get("NAME")
        db_user = db_config.get("USER")
        db_pass = db_config.get("PASSWORD", "")
        db_host = db_config.get("HOST", "127.0.0.1")
        db_port = str(db_config.get("PORT", "5432"))
        if not db_name or not db_user:
            return HttpResponse("Configuracion de base de datos incompleta.", status=500)

        env = os.environ.copy()
        env["PGPASSWORD"] = str(db_pass)
        dump_cmd = [
            "pg_dump",
            "-h",
            str(db_host),
            "-p",
            db_port,
            "-U",
            str(db_user),
            "-d",
            str(db_name),
            "--no-owner",
            "--no-privileges",
        ]
        try:
            dump_result = subprocess.run(
                dump_cmd,
                env=env,
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            return HttpResponse("pg_dump no esta disponible en el servidor.", status=500)
        except subprocess.CalledProcessError as exc:
            error_msg = exc.stderr.decode("utf-8", errors="ignore")[:500]
            return HttpResponse(f"No se pudo generar el respaldo: {error_msg}", status=500)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.sql"
            zip_file.writestr(backup_name, dump_result.stdout)

        buffer.seek(0)
        timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="backup_{timestamp}.zip"'
        return response
