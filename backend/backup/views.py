import io
import os
import shutil
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
        password = str(request.data.get("password", ""))
        if not password or not request.user.check_password(password):
            return HttpResponse("Contrasena incorrecta.", status=403)

        db_config = settings.DATABASES.get("default", {})
        engine = db_config.get("ENGINE", "")
        timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")

        if "sqlite" in engine:
            db_name = db_config.get("NAME")
            if not db_name or not os.path.exists(db_name):
                return HttpResponse("Base SQLite no encontrada.", status=500)

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                backup_name = f"backup_{timestamp}.sqlite3"
                zip_file.write(db_name, arcname=backup_name)

            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="backup_{timestamp}.zip"'
            return response

        if "postgresql" not in engine:
            return HttpResponse("Motor de base de datos no soportado para respaldo.", status=400)

        db_name = db_config.get("NAME")
        db_user = db_config.get("USER")
        db_pass = db_config.get("PASSWORD", "")
        db_host = db_config.get("HOST", "127.0.0.1")
        db_port = str(db_config.get("PORT", "5432"))
        if not db_name or not db_user:
            return HttpResponse("Configuracion de base de datos incompleta.", status=500)

        dump_result = None
        pg_dump_bin = shutil.which("pg_dump")
        if not pg_dump_bin:
            known_paths = [
                "/opt/homebrew/opt/libpq/bin/pg_dump",  # macOS Apple Silicon (brew)
                "/usr/local/opt/libpq/bin/pg_dump",     # macOS Intel (brew)
                "/opt/local/lib/postgresql16/bin/pg_dump",  # MacPorts common
            ]
            for candidate in known_paths:
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    pg_dump_bin = candidate
                    break
        if pg_dump_bin:
            env = os.environ.copy()
            env["PGPASSWORD"] = str(db_pass)
            dump_cmd = [
                pg_dump_bin,
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
            except subprocess.CalledProcessError as exc:
                error_msg = exc.stderr.decode("utf-8", errors="ignore")[:500]
                return HttpResponse(f"No se pudo generar el respaldo: {error_msg}", status=500)
        else:
            project_dir = str(settings.BASE_DIR.parent)
            docker_commands = [
                [
                    "docker",
                    "compose",
                    "exec",
                    "-T",
                    "db",
                    "pg_dump",
                    "-U",
                    str(db_user),
                    "-d",
                    str(db_name),
                    "--no-owner",
                    "--no-privileges",
                ],
                [
                    "docker-compose",
                    "exec",
                    "-T",
                    "db",
                    "pg_dump",
                    "-U",
                    str(db_user),
                    "-d",
                    str(db_name),
                    "--no-owner",
                    "--no-privileges",
                ],
            ]
            last_error = ""
            for cmd in docker_commands:
                try:
                    dump_result = subprocess.run(
                        cmd,
                        check=True,
                        capture_output=True,
                        cwd=project_dir,
                    )
                    break
                except FileNotFoundError:
                    continue
                except subprocess.CalledProcessError as exc:
                    last_error = exc.stderr.decode("utf-8", errors="ignore")[:500]
                    continue

            if dump_result is None:
                if last_error:
                    return HttpResponse(
                        f"No se pudo generar el respaldo con Docker: {last_error}",
                        status=500,
                    )
                return HttpResponse("pg_dump no esta disponible en el servidor.", status=500)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            backup_name = f"backup_{timestamp}.sql"
            zip_file.writestr(backup_name, dump_result.stdout)

        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="backup_{timestamp}.zip"'
        return response
