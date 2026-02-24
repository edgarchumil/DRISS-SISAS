from datetime import datetime
from pathlib import Path

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import MedicationAccessPermission
from medications.models import Medication, Municipality, Movement, MunicipalityStock

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
        total_egresos = 0
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
                total_egresos += 1

        return Response(
            {
                "municipality_id": municipality.id,
                "municipality_name": municipality.name,
                "year": year_value,
                "month": month_value,
                "total_quantity": total_quantity,
                "total_ingresos": total_ingresos,
                "total_egresos": total_egresos,
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

        if str(municipality_id).lower() == "all":
            # Compatibilidad: permite descargar consolidado usando el endpoint
            # base /download/ con municipality_id=all.
            return AllMunicipalitiesMonthlyReportDownloadView().get(request)

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
        total_egresos = sum(1 for item in movements if item.type == "egreso")

        summary_data = [
            ["", f"Total de movimientos: {total_movements}", "", f"Ingresos: {total_ingresos}", "", f"Egresos: {total_egresos}"],
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
                    "Ingreso" if item.type == "ingreso" else "Egreso",
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
            total_egresos = sum(1 for item in movements if item.type == "egreso")
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


class AllMunicipalitiesMonthlyReportDownloadView(APIView):
    permission_classes = [IsAuthenticated, MedicationAccessPermission]

    def get(self, request):
        month = request.query_params.get("month")
        export_format = (request.query_params.get("export_format") or "pdf").lower()
        year_value, month_value = parse_month(month)
        if not year_value or not month_value:
            year_value, month_value = parse_month(None)

        movements = (
            Movement.objects.filter(
                created_at__year=year_value,
                created_at__month=month_value,
            )
            .select_related("medication", "user", "municipality")
            .order_by("municipality__name", "created_at", "id")
        )

        rows = []
        for index, movement in enumerate(movements, start=1):
            user_name = movement.user.get_full_name() or movement.user.username if movement.user else "-"
            rows.append(
                [
                    index,
                    movement.municipality.name if movement.municipality else "-",
                    movement.medication.code,
                    movement.medication.category,
                    movement.medication.material_name,
                    "Ingreso" if movement.type == "ingreso" else "Egreso",
                    user_name,
                    movement.quantity,
                ]
            )

        if export_format == "excel":
            return self._build_excel(rows, year_value, month_value, request)
        return self._build_pdf(movements, year_value, month_value, request)

    def _build_excel(self, rows, year_value: int, month_value: int, request):
        try:
            from io import BytesIO
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
            from openpyxl.utils import get_column_letter
        except Exception:
            return Response(
                {"detail": "Instala openpyxl para generar EXCEL (pip install openpyxl)."},
                status=500,
            )

        from django.db.models import Sum

        wb = Workbook()

        header_fill = PatternFill(start_color="1F4F9C", end_color="1F4F9C", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        header_alignment = Alignment(horizontal="center", vertical="center")
        centered_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        title_font = Font(bold=True)

        def style_header(sheet, row_index: int, col_letters: list[str]):
            for col in col_letters:
                cell = sheet[f"{col}{row_index}"]
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment

        def apply_table_format(sheet, header_row: int, col_letters: list[str]):
            last_row = sheet.max_row
            min_col = ord(col_letters[0]) - ord("A") + 1
            max_col = ord(col_letters[-1]) - ord("A") + 1
            for row in sheet.iter_rows(min_row=header_row + 1, max_row=last_row, min_col=min_col, max_col=max_col):
                for cell in row:
                    cell.alignment = centered_alignment

            for col in col_letters:
                sheet[f"{col}{header_row}"].alignment = header_alignment

            sheet.row_dimensions[header_row].height = 22
            for row_idx in range(header_row + 1, last_row + 1):
                sheet.row_dimensions[row_idx].height = 20

            sheet.auto_filter.ref = f"{col_letters[0]}{header_row}:{col_letters[-1]}{last_row}"
            sheet.freeze_panes = f"{col_letters[0]}{header_row + 1}"
            sheet.print_options.horizontalCentered = True

        # Detail data maps
        month_label = format_period(year_value, month_value)
        downloaded_by = request.user.get_full_name() or request.user.username
        footer_label = f"Descargado por: {downloaded_by} | Generado por: SISAS"
        movements = Movement.objects.filter(
            created_at__year=year_value,
            created_at__month=month_value,
            municipality__isnull=False,
        ).select_related("municipality", "medication")

        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        egresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="egreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        stock_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in MunicipalityStock.objects.values("municipality__id", "municipality__name")
            .annotate(total=Sum("stock"))
        }

        # Sheet 1: General summary
        start_col_idx = 3  # C
        start_col = get_column_letter(start_col_idx)
        general_cols = [get_column_letter(start_col_idx + i) for i in range(6)]  # C:H
        title_row_1 = 5
        title_row_2 = 6
        period_row = 7
        date_row = 8
        meta_row = 9
        table_header_row = 10

        ws = wb.active
        ws.title = "Detalle general"
        ws.merge_cells(f"{general_cols[0]}{title_row_1}:{general_cols[-1]}{title_row_1}")
        ws.merge_cells(f"{general_cols[0]}{title_row_2}:{general_cols[-1]}{title_row_2}")
        ws.merge_cells(f"{general_cols[0]}{period_row}:{general_cols[-1]}{period_row}")
        ws.merge_cells(f"{general_cols[0]}{date_row}:{general_cols[-1]}{date_row}")
        ws.merge_cells(f"{general_cols[0]}{meta_row}:{general_cols[-1]}{meta_row}")

        ws[f"{general_cols[0]}{title_row_1}"] = "DIRECCION DE AREA DE SALUD DE SOLOLÁ"
        ws[f"{general_cols[0]}{title_row_2}"] = "REPORTE MENSUAL DE INSUMOS / MATERIALES"
        ws[f"{general_cols[0]}{period_row}"] = f"Periodo: {month_label}"
        ws[f"{general_cols[0]}{date_row}"] = f"Fecha: {timezone.localdate().strftime('%d/%m/%Y')}"
        ws[f"{general_cols[0]}{meta_row}"] = footer_label

        ws[f"{general_cols[0]}{title_row_1}"].font = title_font
        ws[f"{general_cols[0]}{title_row_2}"].font = title_font
        ws[f"{general_cols[0]}{title_row_1}"].alignment = centered_alignment
        ws[f"{general_cols[0]}{title_row_2}"].alignment = centered_alignment
        ws[f"{general_cols[0]}{period_row}"].alignment = centered_alignment
        ws[f"{general_cols[0]}{date_row}"].alignment = centered_alignment
        ws[f"{general_cols[0]}{meta_row}"].alignment = centered_alignment

        for col_idx, value in enumerate(["No.", "Municipio", "Insumo", "Ingresos", "Salidas (Egresos)", "Existencias"]):
            ws.cell(row=table_header_row, column=start_col_idx + col_idx, value=value)
        style_header(ws, table_header_row, general_cols)

        from django.db.models import Sum, Case, When, IntegerField

        movements_summary = movements.values("municipality_id", "medication_id").annotate(
            ingresos=Sum(Case(When(type="ingreso", then="quantity"), default=0, output_field=IntegerField())),
            egresos=Sum(Case(When(type="egreso", then="quantity"), default=0, output_field=IntegerField())),
        )
        movement_map = {
            (row["municipality_id"], row["medication_id"]): (row["ingresos"] or 0, row["egresos"] or 0)
            for row in movements_summary
        }
        stock_map = {
            (row["municipality_id"], row["medication_id"]): row["total"] or 0
            for row in MunicipalityStock.objects.values("municipality_id", "medication_id")
            .annotate(total=Sum("stock"))
        }

        keys = set(movement_map.keys()) | set(stock_map.keys())
        municipality_ids = {k[0] for k in keys if k[0] is not None}
        medication_ids = {k[1] for k in keys if k[1] is not None}
        municipalities = {
            m.id: m.name for m in Municipality.objects.filter(id__in=municipality_ids)
        }
        medications = {
            m.id: m.material_name for m in Medication.objects.filter(id__in=medication_ids)
        }

        def sort_key(item):
            mid, medid = item
            return (municipalities.get(mid, ""), medications.get(medid, ""))

        for index, (municipality_id, medication_id) in enumerate(sorted(keys, key=sort_key), start=1):
            mun_name = municipalities.get(municipality_id, "-")
            med_name = medications.get(medication_id, "-")
            ingresos_total, egresos_total = movement_map.get((municipality_id, medication_id), (0, 0))
            stock_total = stock_map.get((municipality_id, medication_id), 0)
            row_idx = ws.max_row + 1
            values = [index, mun_name, med_name, ingresos_total, egresos_total, stock_total]
            for col_idx, value in enumerate(values):
                ws.cell(row=row_idx, column=start_col_idx + col_idx, value=value)

        ws.column_dimensions["C"].width = 7
        ws.column_dimensions["D"].width = 24
        ws.column_dimensions["E"].width = 34
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 16
        ws.column_dimensions["H"].width = 12
        apply_table_format(ws, table_header_row, general_cols)

        # One sheet per municipality with summary
        for municipality_id, municipality_name in sorted(municipalities.items(), key=lambda item: item[1]):
            # Excel sheet title max length 31 and no invalid chars
            safe_title = "".join(ch for ch in municipality_name if ch not in '\\/*?:[]')
            safe_title = safe_title[:31] if safe_title else f"Municipio {municipality_id}"
            sheet = wb.create_sheet(title=safe_title)
            muni_start_col_idx = 3  # C
            muni_cols = [get_column_letter(muni_start_col_idx + i) for i in range(4)]  # C:F
            muni_title_row_1 = 5
            muni_title_row_2 = 6
            muni_name_row = 7
            muni_period_row = 8
            muni_date_row = 9
            muni_meta_row = 10
            muni_table_header_row = 11

            sheet.merge_cells(f"{muni_cols[0]}{muni_title_row_1}:{muni_cols[-1]}{muni_title_row_1}")
            sheet.merge_cells(f"{muni_cols[0]}{muni_title_row_2}:{muni_cols[-1]}{muni_title_row_2}")
            sheet.merge_cells(f"{muni_cols[0]}{muni_name_row}:{muni_cols[-1]}{muni_name_row}")
            sheet.merge_cells(f"{muni_cols[0]}{muni_period_row}:{muni_cols[-1]}{muni_period_row}")
            sheet.merge_cells(f"{muni_cols[0]}{muni_date_row}:{muni_cols[-1]}{muni_date_row}")
            sheet.merge_cells(f"{muni_cols[0]}{muni_meta_row}:{muni_cols[-1]}{muni_meta_row}")

            sheet[f"{muni_cols[0]}{muni_title_row_1}"] = "DIRECCION DE AREA DE SALUD DE SOLOLÁ"
            sheet[f"{muni_cols[0]}{muni_title_row_2}"] = "REPORTE MENSUAL DE INSUMOS / MATERIALES"
            sheet[f"{muni_cols[0]}{muni_name_row}"] = f"Municipio: {municipality_name}"
            sheet[f"{muni_cols[0]}{muni_period_row}"] = f"Periodo: {month_label}"
            sheet[f"{muni_cols[0]}{muni_date_row}"] = f"Fecha: {timezone.localdate().strftime('%d/%m/%Y')}"
            sheet[f"{muni_cols[0]}{muni_meta_row}"] = footer_label

            sheet[f"{muni_cols[0]}{muni_title_row_1}"].font = title_font
            sheet[f"{muni_cols[0]}{muni_title_row_2}"].font = title_font
            sheet[f"{muni_cols[0]}{muni_title_row_1}"].alignment = centered_alignment
            sheet[f"{muni_cols[0]}{muni_title_row_2}"].alignment = centered_alignment
            sheet[f"{muni_cols[0]}{muni_name_row}"].alignment = centered_alignment
            sheet[f"{muni_cols[0]}{muni_period_row}"].alignment = centered_alignment
            sheet[f"{muni_cols[0]}{muni_date_row}"].alignment = centered_alignment
            sheet[f"{muni_cols[0]}{muni_meta_row}"].alignment = centered_alignment

            for col_idx, value in enumerate(["Insumo", "Ingresos", "Salidas (Egresos)", "Existencias"]):
                sheet.cell(row=muni_table_header_row, column=muni_start_col_idx + col_idx, value=value)
            style_header(sheet, muni_table_header_row, muni_cols)
            municipality_keys = [k for k in keys if k[0] == municipality_id]
            for med_id in sorted(municipality_keys, key=lambda k: medications.get(k[1], "")):
                med_name = medications.get(med_id[1], "-")
                ingresos_total, egresos_total = movement_map.get((municipality_id, med_id[1]), (0, 0))
                stock_total = stock_map.get((municipality_id, med_id[1]), 0)
                row_idx = sheet.max_row + 1
                values = [med_name, ingresos_total, egresos_total, stock_total]
                for col_idx, value in enumerate(values):
                    sheet.cell(row=row_idx, column=muni_start_col_idx + col_idx, value=value)
            sheet.column_dimensions["C"].width = 34
            sheet.column_dimensions["D"].width = 12
            sheet.column_dimensions["E"].width = 16
            sheet.column_dimensions["F"].width = 12
            apply_table_format(sheet, muni_table_header_row, muni_cols)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        filename = f"reporte_todos_municipios_{year_value}-{month_value:02d}.xlsx"
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _build_pdf(self, movements, year_value: int, month_value: int, request):
        try:
            from io import BytesIO
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except Exception:
            return Response(
                {"detail": "Instala reportlab para generar PDF (pip install reportlab)."},
                status=500,
            )

        from django.db.models import Sum

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=20, bottomMargin=20, leftMargin=36, rightMargin=36)
        styles = getSampleStyleSheet()
        elements = []

        period_label = format_period(year_value, month_value)
        username = request.user.get_full_name() or request.user.username
        date_label = timezone.localdate().strftime("%d/%m/%Y")

        total_movements = movements.count()
        total_ingresos = movements.filter(type="ingreso").count()
        total_egresos = movements.filter(type="egreso").count()

        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        ingresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="ingreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        egresos_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in movements.filter(type="egreso")
            .values("municipality__id", "municipality__name")
            .annotate(total=Sum("quantity"))
        }
        stock_map = {
            (row["municipality__id"], row["municipality__name"]): row["total"] or 0
            for row in MunicipalityStock.objects.values("municipality__id", "municipality__name")
            .annotate(total=Sum("stock"))
        }

        # Map of municipality -> list of insumos (material_name) for the month
        materials_map: dict[tuple[int | None, str | None], list[str]] = {}
        for row in movements.values(
            "municipality__id", "municipality__name", "medication__material_name"
        ).distinct():
            key = (row["municipality__id"], row["municipality__name"])
            materials_map.setdefault(key, []).append(row["medication__material_name"])

        def format_materials(key: tuple[int | None, str | None], limit: int = 5) -> str:
            items = sorted(materials_map.get(key, []))
            if not items:
                return "-"
            if len(items) <= limit:
                return ", ".join(items)
            extra = len(items) - limit
            return f"{', '.join(items[:limit])} (+{extra})"

        from django.db.models import Sum, Case, When, IntegerField

        movements = movements.filter(municipality__isnull=False)
        movements_summary = movements.values("municipality_id", "medication_id").annotate(
            ingresos=Sum(Case(When(type="ingreso", then="quantity"), default=0, output_field=IntegerField())),
            egresos=Sum(Case(When(type="egreso", then="quantity"), default=0, output_field=IntegerField())),
        )
        movement_map = {
            (row["municipality_id"], row["medication_id"]): (row["ingresos"] or 0, row["egresos"] or 0)
            for row in movements_summary
        }
        stock_map = {
            (row["municipality_id"], row["medication_id"]): row["total"] or 0
            for row in MunicipalityStock.objects.values("municipality_id", "medication_id")
            .annotate(total=Sum("stock"))
        }
        keys = set(movement_map.keys()) | set(stock_map.keys())
        municipality_ids = {k[0] for k in keys if k[0] is not None}
        medication_ids = {k[1] for k in keys if k[1] is not None}
        municipalities = {m.id: m.name for m in Municipality.objects.filter(id__in=municipality_ids)}
        medications = {m.id: m.material_name for m in Medication.objects.filter(id__in=medication_ids)}

        def sort_key(item):
            mid, medid = item
            return (municipalities.get(mid, ""), medications.get(medid, ""))

        data = [["No.", "Municipio", "Insumo", "Ingresos", "Salidas (Egresos)", "Existencias"]]
        for index, (municipality_id, medication_id) in enumerate(sorted(keys, key=sort_key), start=1):
            mun_name = municipalities.get(municipality_id, "-")
            med_name = medications.get(medication_id, "-")
            ingresos_total, egresos_total = movement_map.get((municipality_id, medication_id), (0, 0))
            stock_total = stock_map.get((municipality_id, medication_id), 0)
            data.append(
                [
                    str(index),
                    mun_name,
                    med_name,
                    str(ingresos_total),
                    str(egresos_total),
                    str(stock_total),
                ]
            )

        table = Table(data, hAlign="CENTER", colWidths=[30, 160, 240, 70, 90, 90])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4f9c")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e6")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fb")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 0), (2, -1), "LEFT"),
                    ("ALIGN", (3, 0), (5, -1), "RIGHT"),
                ]
            )
        )
        elements.append(table)

        def draw_header(canvas_obj, doc_obj):
            canvas_obj.saveState()
            width, height = landscape(letter)

            # Top light bar
            canvas_obj.setFillColor(colors.HexColor("#dcecff"))
            canvas_obj.rect(0, height - 30, width, 30, fill=1, stroke=0)
            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.setFillColor(colors.HexColor("#0f2c5c"))
            canvas_obj.drawCentredString(width / 2, height - 20, "DIRECCION DE AREA DE SALUD DE SOLOLÁ")

            # Main title bar
            canvas_obj.setFillColor(colors.HexColor("#1f4f9c"))
            canvas_obj.rect(0, height - 95, width, 55, fill=1, stroke=0)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.setFont("Helvetica-Bold", 14)
            canvas_obj.drawCentredString(width / 2, height - 60, "REPORTE MENSUAL DE")
            canvas_obj.drawCentredString(width / 2, height - 78, "INSUMOS / MATERIALES")

            # Info box
            canvas_obj.setFillColor(colors.HexColor("#eef3fb"))
            info_top = height - 115
            info_box_width = width - 120
            info_box_x = (width - info_box_width) / 2
            canvas_obj.roundRect(info_box_x, info_top - 45, info_box_width, 45, 8, fill=1, stroke=0)
            canvas_obj.setFillColor(colors.HexColor("#0f2c5c"))
            canvas_obj.setFont("Helvetica-Bold", 9)
            left_x = info_box_x + 20
            right_x = info_box_x + info_box_width / 2 + 20
            canvas_obj.drawString(left_x, info_top - 20, "Municipio: DMS Y DRISS Local")
            canvas_obj.drawString(left_x, info_top - 35, f"Periodo: {period_label}")
            canvas_obj.drawString(right_x, info_top - 20, f"Fecha: {date_label}")
            canvas_obj.drawString(right_x, info_top - 35, f"Usuario: {username}")

            # Summary pills
            pill_top = info_top - 58
            pill_height = 18
            pill_widths = [180, 120, 120]
            pill_labels = [
                f"Total de movimientos: {total_movements}",
                f"Ingresos: {total_ingresos}",
                f"Egresos: {total_egresos}",
            ]
            total_pills_width = sum(pill_widths) + (len(pill_widths) - 1) * 14
            x = (width - total_pills_width) / 2
            for label, w in zip(pill_labels, pill_widths):
                canvas_obj.setFillColor(colors.HexColor("#eef3fb"))
                canvas_obj.roundRect(x, pill_top - pill_height, w, pill_height, 6, fill=1, stroke=0)
                canvas_obj.setFillColor(colors.HexColor("#0f2c5c"))
                canvas_obj.setFont("Helvetica-Bold", 8)
                canvas_obj.drawCentredString(x + w / 2, pill_top - 12, label)
                x += w + 14

            canvas_obj.restoreState()

        # Leave space for header block
        elements.insert(0, Spacer(1, 175))

        doc.build(elements, onFirstPage=draw_header)
        pdf = buffer.getvalue()
        buffer.close()

        filename = f"reporte_todos_municipios_{year_value}-{month_value:02d}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
