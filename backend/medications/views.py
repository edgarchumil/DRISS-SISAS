import time
import unicodedata

from django.db import models, transaction
from django.db.utils import OperationalError
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.utils import timezone

from accounts.permissions import MedicationAccessPermission
from medications.models import Medication, Municipality, MunicipalityStock, Movement
from medications.serializers import (
    MedicationSerializer,
    MunicipalitySerializer,
    MunicipalityStockSerializer,
    MovementSerializer,
)


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all().order_by("material_name")
    serializer_class = MedicationSerializer
    permission_classes = [MedicationAccessPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "material_name"]

class MunicipalityViewSet(viewsets.ModelViewSet):
    queryset = Municipality.objects.all().order_by("name")
    serializer_class = MunicipalitySerializer
    permission_classes = [MedicationAccessPermission]

    @action(detail=True, methods=["get"])
    def stock(self, request, pk=None):
        municipality = self.get_object()
        total_stock = (
            MunicipalityStock.objects.filter(municipality=municipality)
            .aggregate(total=models.Sum("stock"))
            .get("total")
            or 0
        )
        return Response(
            {
                "municipality_id": municipality.id,
                "municipality_name": municipality.name,
                "total_stock": total_stock,
            }
        )

    @action(detail=True, methods=["get"])
    def stocks(self, request, pk=None):
        municipality = self.get_object()
        medication_ids = set(Medication.objects.values_list("id", flat=True))
        existing_ids = set(
            MunicipalityStock.objects.filter(municipality=municipality).values_list(
                "medication_id", flat=True
            )
        )
        missing_ids = medication_ids - existing_ids
        if missing_ids:
            MunicipalityStock.objects.bulk_create(
                [
                    MunicipalityStock(
                        municipality=municipality, medication_id=med_id, stock=0
                    )
                    for med_id in missing_ids
                ]
            )

        queryset = MunicipalityStock.objects.filter(municipality=municipality).select_related(
            "municipality", "medication"
        )
        serializer = MunicipalityStockSerializer(queryset, many=True)
        return Response(serializer.data)


class MunicipalityStockViewSet(viewsets.ModelViewSet):
    queryset = MunicipalityStock.objects.all().order_by("municipality__name", "medication__material_name")
    serializer_class = MunicipalityStockSerializer
    permission_classes = [MedicationAccessPermission]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        data = (
            MunicipalityStock.objects.values("medication_id")
            .annotate(total_stock=models.Sum("stock"))
            .order_by("medication_id")
        )
        return Response(list(data))

    def create(self, request, *args, **kwargs):
        municipality_id = request.data.get("municipality")
        medication_id = request.data.get("medication")
        stock = request.data.get("stock", 0)

        try:
            municipality_id = int(str(municipality_id).strip())
            medication_id = int(str(medication_id).strip())
            stock = int(float(str(stock).strip()))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Municipio, medicamento y stock deben ser numeros validos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if municipality_id <= 0 or medication_id <= 0:
            return Response(
                {"detail": "Municipio y medicamento son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if stock < 0:
            return Response(
                {"detail": "El stock no puede ser negativo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            municipality = Municipality.objects.get(pk=municipality_id)
        except Municipality.DoesNotExist:
            return Response(
                {"detail": "Municipio no existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            medication = Medication.objects.get(pk=medication_id)
        except Medication.DoesNotExist:
            return Response(
                {"detail": "Medicamento no existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def apply_stock():
            with transaction.atomic():
                instance, created = MunicipalityStock.objects.update_or_create(
                    municipality=municipality,
                    medication=medication,
                    defaults={"stock": max(0, stock)},
                )
            return instance, created

        result = self._with_retry(apply_stock)
        if isinstance(result, Response):
            return result

        instance, created = result
        output = self.get_serializer(instance)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(output.data, status=status_code)

    def _with_retry(self, fn, retries=5, base_delay=0.1):
        last_error = None
        for attempt in range(retries):
            try:
                return fn()
            except OperationalError as exc:
                last_error = exc
                if "database is locked" not in str(exc).lower():
                    raise
                time.sleep(base_delay * (attempt + 1))
        return Response(
            {"detail": "Base de datos ocupada. Intenta de nuevo."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class MovementViewSet(viewsets.ModelViewSet):
    queryset = Movement.objects.select_related("medication", "municipality", "user").all()
    serializer_class = MovementSerializer
    permission_classes = [MedicationAccessPermission]

    @action(detail=False, methods=["post"], url_path="dispatch-report")
    def dispatch_report(self, request):
        ids = request.data.get("ids")
        if not ids or not isinstance(ids, list):
            return Response({"detail": "ids es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        movements = (
            Movement.objects.filter(id__in=ids)
            .select_related("medication", "municipality", "user")
            .order_by("id")
        )
        if not movements.exists():
            return Response({"detail": "Movimientos no encontrados."}, status=status.HTTP_404_NOT_FOUND)

        try:
            from io import BytesIO
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        except Exception:
            return Response(
                {"detail": "Instala reportlab para generar PDF (pip install reportlab)."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        municipality = movements.first().municipality
        username = request.user.get_full_name() or request.user.username
        date_label = timezone.localdate().strftime("%d/%m/%Y")

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=230, bottomMargin=60)
        styles = getSampleStyleSheet()
        elements = []

        data = [["No.", "Codigo", "Categoria", "Material medico", "Cantidad"]]
        row_index = 1
        for movement in movements:
            data.append(
                [
                    str(row_index),
                    movement.medication.code,
                    movement.medication.category,
                    movement.medication.material_name,
                    str(movement.quantity),
                ]
            )
            row_index += 1

        table = Table(data, hAlign="CENTER", colWidths=[35, 70, 80, 280, 70])
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
                    ("ALIGN", (4, 0), (4, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(Spacer(1, 8))
        elements.append(table)
        elements.append(Spacer(1, 10))
        notes_text = movements.first().notes or "-"
        notes_style = styles["Normal"].clone("notes_style")
        notes_style.fontSize = 9
        elements.append(Paragraph(f"Observaciones: {notes_text}", notes_style))

        footer_style = styles["Normal"].clone("footer_style")
        footer_style.alignment = 1
        footer_style.fontSize = 9
        elements.append(Spacer(1, 18))
        elements.append(Paragraph("Despacho generado automaticamente por el sistema SISAS", footer_style))

        def draw_header(canvas_obj, doc_obj):
            canvas_obj.saveState()
            width, height = letter
            header_top = height - 40
            canvas_obj.setFillColor(colors.HexColor("#1f4f9c"))
            canvas_obj.rect(0, header_top - 90, width, 90, fill=1, stroke=0)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawCentredString(width / 2, header_top - 40, "DESPACHO DE INSUMOS")
            canvas_obj.setFont("Helvetica-Bold", 20)
            canvas_obj.drawCentredString(width / 2, header_top - 65, "INSUMOS / MATERIALES")

            canvas_obj.setFillColor(colors.HexColor("#0f2c5c"))
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawCentredString(
                width / 2,
                height - 15,
                "DIRECCION DE AREA DE SALUD DE SOLOLÁ",
            )

            canvas_obj.setFillColor(colors.HexColor("#eef3fb"))
            info_box_top = header_top - 105
            canvas_obj.roundRect(60, info_box_top - 45, width - 120, 45, 8, fill=1, stroke=0)
            canvas_obj.setFillColor(colors.HexColor("#0f2c5c"))
            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.drawString(80, info_box_top - 20, f"Municipio: {municipality.name if municipality else '-'}")
            canvas_obj.drawString(80, info_box_top - 35, f"Fecha: {date_label}")
            canvas_obj.drawString(width / 2 + 10, info_box_top - 20, f"Usuario: {username}")
            canvas_obj.restoreState()

        doc.build(elements, onFirstPage=draw_header)
        pdf = buffer.getvalue()
        buffer.close()

        filename = f"despacho_{municipality.name if municipality else 'municipio'}_{timezone.localdate():%Y%m%d}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=["post"])
    def bulk(self, request):
        items = request.data if isinstance(request.data, list) else request.data.get("items")
        if not items or not isinstance(items, list):
            return Response(
                {"detail": "Se requiere una lista de movimientos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        municipality_name = ""
        if hasattr(request.user, "profile"):
            municipality_name = (request.user.profile.municipality or "").strip()

        def normalize(text: str) -> str:
            normalized = unicodedata.normalize("NFKD", text)
            return "".join([char for char in normalized if not unicodedata.combining(char)]).lower().strip()

        default_municipality = None
        if municipality_name:
            normalized_name = normalize(municipality_name)
            default_municipality = Municipality.objects.filter(name__iexact=municipality_name).first()
            if not default_municipality and normalized_name:
                for existing in Municipality.objects.all():
                    if normalize(existing.name) == normalized_name:
                        default_municipality = existing
                        break
            if not default_municipality:
                default_municipality = Municipality.objects.create(name=municipality_name)

        prepared = []
        municipality_cache = {}
        for item in items:
            movement_type = str(item.get("type", "")).strip().lower()
            medication_id = item.get("medication")
            quantity = item.get("quantity")
            notes = str(item.get("notes", "")).strip()
            municipality_id = item.get("municipality")

            if movement_type not in {"ingreso", "egreso"}:
                return Response(
                    {"detail": "Tipo de movimiento invalido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                medication_id = int(str(medication_id).strip())
                quantity = int(float(str(quantity).strip()))
                municipality_id = (
                    int(str(municipality_id).strip())
                    if municipality_id is not None and str(municipality_id).strip() != ""
                    else None
                )
            except (TypeError, ValueError):
                return Response(
                    {"detail": "Medicamento y cantidad deben ser numeros validos."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if medication_id <= 0 or quantity <= 0:
                return Response(
                    {"detail": "Medicamento y cantidad deben ser mayores a cero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            municipality = None
            if municipality_id:
                if municipality_id not in municipality_cache:
                    municipality_cache[municipality_id] = Municipality.objects.filter(
                        pk=municipality_id
                    ).first()
                municipality = municipality_cache[municipality_id]
                if not municipality:
                    return Response(
                        {"detail": "Municipio no existe."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if not default_municipality:
                    return Response(
                        {"detail": "El usuario no tiene municipio asignado."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                municipality = default_municipality

            prepared.append(
                {
                    "type": movement_type,
                    "medication_id": medication_id,
                    "quantity": quantity,
                    "notes": notes,
                    "municipality": municipality,
                }
            )

        def apply_movements():
            with transaction.atomic():
                movements = []
                for item in prepared:
                    medication = (
                        Medication.objects.select_for_update()
                        .filter(pk=item["medication_id"])
                        .first()
                    )
                    if not medication:
                        return Response(
                            {"detail": "Medicamento no existe."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    municipality_stock = MunicipalityStock.objects.select_for_update().filter(
                        municipality=item["municipality"], medication=medication
                    ).first()
                    if not municipality_stock:
                        municipality_stock = MunicipalityStock.objects.create(
                            municipality=item["municipality"], medication=medication, stock=0
                        )

                    if item["type"] == "egreso":
                        if municipality_stock.stock < item["quantity"]:
                            return Response(
                                {"detail": "Stock insuficiente en el municipio."},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        municipality_stock.stock -= item["quantity"]
                    else:
                        municipality_stock.stock += item["quantity"]

                    municipality_stock.save(update_fields=["stock", "updated_at"])
                    medication.physical_stock = (
                        MunicipalityStock.objects.filter(medication=medication).aggregate(
                            total=models.Sum("stock")
                        ).get("total")
                        or 0
                    )
                    medication.save(update_fields=["physical_stock", "updated_at"])

                    movement = Movement.objects.create(
                        type=item["type"],
                        medication=medication,
                        municipality=item["municipality"],
                        user=request.user,
                        quantity=item["quantity"],
                        notes=item["notes"],
                    )
                    movements.append(movement)
            return movements

        movements = self._with_retry(apply_movements)
        if isinstance(movements, Response):
            return movements

        serializer = self.get_serializer(movements, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        movement_type = str(request.data.get("type", "")).strip().lower()
        medication_id = request.data.get("medication")
        quantity = request.data.get("quantity")
        notes = str(request.data.get("notes", "")).strip()
        municipality_id = request.data.get("municipality")

        if movement_type not in {"ingreso", "egreso"}:
            return Response(
                {"detail": "Tipo de movimiento invalido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            medication_id = int(str(medication_id).strip())
            quantity = int(float(str(quantity).strip()))
            municipality_id = (
                int(str(municipality_id).strip())
                if municipality_id is not None and str(municipality_id).strip() != ""
                else None
            )
        except (TypeError, ValueError):
            return Response(
                {"detail": "Medicamento y cantidad deben ser numeros validos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if medication_id <= 0:
            return Response(
                {"detail": "Medicamento es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity <= 0:
            return Response(
                {"detail": "La cantidad debe ser mayor a cero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        municipality = None
        if municipality_id:
            municipality = Municipality.objects.filter(pk=municipality_id).first()
            if not municipality:
                return Response(
                    {"detail": "Municipio no existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            municipality_name = ""
            if hasattr(request.user, "profile"):
                municipality_name = (request.user.profile.municipality or "").strip()

            if not municipality_name:
                return Response(
                    {"detail": "El usuario no tiene municipio asignado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            def normalize(text: str) -> str:
                normalized = unicodedata.normalize("NFKD", text)
                return "".join([char for char in normalized if not unicodedata.combining(char)]).lower().strip()

            normalized_name = normalize(municipality_name)
            municipality = Municipality.objects.filter(name__iexact=municipality_name).first()
            if not municipality and normalized_name:
                for existing in Municipality.objects.all():
                    if normalize(existing.name) == normalized_name:
                        municipality = existing
                        break
            if not municipality:
                municipality = Municipality.objects.create(name=municipality_name)

        def apply_single():
            with transaction.atomic():
                medication = (
                    Medication.objects.select_for_update()
                    .filter(pk=medication_id)
                    .first()
                )
                if not medication:
                    return Response(
                        {"detail": "Medicamento no existe."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                municipality_stock = MunicipalityStock.objects.select_for_update().filter(
                    municipality=municipality, medication=medication
                ).first()
                if not municipality_stock:
                    municipality_stock = MunicipalityStock.objects.create(
                        municipality=municipality, medication=medication, stock=0
                    )

                if movement_type == "egreso":
                    if municipality_stock.stock < quantity:
                        return Response(
                            {"detail": "Stock insuficiente en el municipio."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    municipality_stock.stock -= quantity
                else:
                    municipality_stock.stock += quantity

                municipality_stock.save(update_fields=["stock", "updated_at"])
                medication.physical_stock = (
                    MunicipalityStock.objects.filter(medication=medication).aggregate(
                        total=models.Sum("stock")
                    ).get("total")
                    or 0
                )
                medication.save(update_fields=["physical_stock", "updated_at"])

                movement = Movement.objects.create(
                    type=movement_type,
                    medication=medication,
                    municipality=municipality,
                    user=request.user,
                    quantity=quantity,
                    notes=notes,
                )
            return movement

        movement = self._with_retry(apply_single)
        if isinstance(movement, Response):
            return movement

        serializer = self.get_serializer(movement)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _with_retry(self, fn, retries=5, base_delay=0.1):
        last_error = None
        for attempt in range(retries):
            try:
                return fn()
            except OperationalError as exc:
                last_error = exc
                if "database is locked" not in str(exc).lower():
                    raise
                time.sleep(base_delay * (attempt + 1))
        return Response(
            {"detail": "Base de datos ocupada. Intenta de nuevo."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
