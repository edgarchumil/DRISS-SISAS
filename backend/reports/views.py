from datetime import datetime
from pathlib import Path

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import MedicationAccessPermission
from medications.models import Municipality, Movement

MONTHS_ES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


def parse_month(value: str | None):
    if not value:
        now = timezone.now()
        return now.year, now.month
    try:
        parsed = datetime.strptime(value, "%Y-%m")
        return parsed.year, parsed.month
    except ValueError:
        return None, None


def format_period(year_value: int, month_value: int) -> str:
    month_name = MONTHS_ES[month_value - 1] if 1 <= month_value <= 12 else str(month_value)
    return f"{month_name} {year_value}"


class MunicipalityMonthlyReportView(APIView):
    permission_classes = [IsAuthenticated, MedicationAccessPermission]

    def get(self, request):
        municipality_id = request.query_params.get("municipality_id")
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        year_value, month_value = parse_month(month)

        if not municipality_id:
            return Response({"detail": "municipality_id es requerido."}, status=400)

        if year and month:
            return Response({"detail": "Usa solo month (YYYY-MM) o year/month."}, status=400)

        if not year_value or not month_value:
            if year and month:
                year_value = int(year)
                month_value = int(month)
            else:
                year_value, month_value = parse_month(None)

        try:
            municipality = Municipality.objects.get(pk=int(municipality_id))
        except (ValueError, Municipality.DoesNotExist):
            return Response({"detail": "Municipio invalido."}, status=400)

        movements = (
            Movement.objects.filter(
                municipality=municipality,
                created_at__year=year_value,
                created_at__month=month_value,
            )
            .select_related("medication", "user")
            .order_by("created_at", "id")
        )
        items = []
        total_quantity = 0
        total_ingresos = 0
        total_pedidos = 0
        for movement in movements:
            user_name = (
                movement.user.get_full_name() or movement.user.username
                if movement.user
                else "-"
            )
            items.append(
                {
                    "code": movement.medication.code,
                    "category": movement.medication.category,
                    "material_name": movement.medication.material_name,
                    "quantity": movement.quantity,
                    "type": movement.type,
                    "user": user_name,
                }
            )
            total_quantity += movement.quantity
            if movement.type == "ingreso":
                total_ingresos += 1
            else:
                total_pedidos += 1

        return Response(
            {
                "municipality_id": municipality.id,
                "municipality_name": municipality.name,
                "year": year_value,
                "month": month_value,
                "total_quantity": total_quantity,
                "total_ingresos": total_ingresos,
                "total_pedidos": total_pedidos,
                "items": items,
            }
        )


class MunicipalityMonthlyReportDownloadView(APIView):
    permission_classes = [IsAuthenticated, MedicationAccessPermission]

    def get(self, request):
        municipality_id = request.query_params.get("municipality_id")
        month = request.query_params.get("month")
        year_value, month_value = parse_month(month)

        if not municipality_id:
            return Response({"detail": "municipality_id es requerido."}, status=400)

        if not year_value or not month_value:
            year_value, month_value = parse_month(None)

        try:
            municipality = Municipality.objects.get(pk=int(municipality_id))
        except (ValueError, Municipality.DoesNotExist):
            return Response({"detail": "Municipio invalido."}, status=400)

        movements = (
            Movement.objects.filter(
                municipality=municipality,
                created_at__year=year_value,
                created_at__month=month_value,
            )
            .select_related("medication", "user")
            .order_by("created_at", "id")
        )
        try:
            from io import BytesIO
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        except Exception:
            return Response(
                {"detail": "Instala reportlab para generar PDF (pip install reportlab)."},
                status=500,
            )

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        elements = []

        total_movements = movements.count()
        total_ingresos = sum(1 for item in movements if item.type == "ingreso")
        total_pedidos = sum(1 for item in movements if item.type == "egreso")

        summary_data = [
            ["", f"Total de movimientos: {total_movements}", "", f"Ingresos: {total_ingresos}", "", f"Pedidos: {total_pedidos}"],
        ]
        summary_table = Table(summary_data, hAlign="CENTER", colWidths=[14, 170, 14, 120, 10, 100])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3fb")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (2, -1), "LEFT"),
                    ("ALIGN", (3, 0), (3, -1), "LEFT"),
                    ("ALIGN", (4, 0), (4, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#1f4f9c")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#1f4f9c")),
                    ("GRID", (0, 0), (-1, -1), 0.0, colors.white),
                ]
            )
        )
        elements.append(Spacer(1, 170))
        elements.append(summary_table)
        elements.append(Spacer(1, 10))

        data = [["No.", "Codigo", "Categoria", "Material medico", "Tipo", "Usuario", "Cantidad"]]
        row_index = 1
        for item in movements:
            user_name = (
                item.user.get_full_name() or item.user.username
                if item.user
                else "-"
            )
            data.append(
                [
                    str(row_index),
                    item.medication.code,
                    item.medication.category,
                    item.medication.material_name,
                    "Ingreso" if item.type == "ingreso" else "Pedido",
                    user_name,
                    str(item.quantity),
                ]
            )
            row_index += 1
        table = Table(data, hAlign="CENTER", colWidths=[30, 55, 60, 175, 60, 150, 55])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4f9c")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e6")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fb")]),
                    ("ALIGN", (0, 0), (2, -1), "CENTER"),
                    ("ALIGN", (3, 0), (3, -1), "LEFT"),
                    ("ALIGN", (4, 0), (6, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#1f4f9c")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#1f4f9c")),
                ]
            )
        )
        elements.append(table)

        footer_style = styles["Normal"].clone("footer_style")
        footer_style.alignment = 1
        footer_style.fontSize = 9
        elements.append(Spacer(1, 18))

        elements.append(Paragraph("Reporte generado automaticamente por el sistema SISAS", footer_style))

        def draw_header(canvas_obj, doc_obj):
            canvas_obj.saveState()
            width, height = letter
            header_top = height - 40
            canvas_obj.setFillColor(colors.HexColor("#1f4f9c"))
            canvas_obj.rect(0, header_top - 90, width, 90, fill=1, stroke=0)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawCentredString(width / 2, header_top - 40, "REPORTE MENSUAL DE")
            canvas_obj.setFont("Helvetica-Bold", 20)
            canvas_obj.drawCentredString(width / 2, header_top - 65, "INSUMOS / MATERIALES")

            canvas_obj.setFillColor(colors.HexColor("#0f2c5c"))
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawCentredString(
                width / 2,
                height - 15,
                "DIRECCION DE AREA DE SALUD DE SOLOLÁ",
            )

            # Info box
            canvas_obj.setFillColor(colors.HexColor("#eef3fb"))
            info_box_top = header_top - 105
            canvas_obj.roundRect(60, info_box_top - 45, width - 120, 45, 8, fill=1, stroke=0)
            canvas_obj.setFillColor(colors.HexColor("#0f2c5c"))
            canvas_obj.setFont("Helvetica-Bold", 10)
            period_label = format_period(year_value, month_value)
            date_label = timezone.localdate().strftime("%d/%m/%Y")
            username = request.user.get_full_name() or request.user.username
            canvas_obj.drawString(80, info_box_top - 20, f"Municipio: {municipality.name}")
            canvas_obj.drawString(80, info_box_top - 35, f"Periodo: {period_label}")
            canvas_obj.drawString(width / 2 + 10, info_box_top - 20, f"Fecha: {date_label}")
            canvas_obj.drawString(width / 2 + 10, info_box_top - 35, f"Usuario: {username}")

            # Summary pills
            total_movements = movements.count()
            total_ingresos = sum(1 for item in movements if item.type == "ingreso")
            total_pedidos = sum(1 for item in movements if item.type == "egreso")
            canvas_obj.setFillColor(colors.HexColor("#eef3fb"))
            # summary moved below table

            # Footer
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.HexColor("#5f6b7a"))
            canvas_obj.drawCentredString(width / 2, 30, "Direccion de Area de Salud de Sololá | 2026")
            canvas_obj.restoreState()

        doc.build(elements, onFirstPage=draw_header)

        pdf = buffer.getvalue()
        buffer.close()

        filename = f"reporte_{municipality.name}_{year_value}-{month_value:02d}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

