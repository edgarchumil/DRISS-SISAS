from django.contrib.auth.models import User
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import ROLE_ADMIN, user_in_group
from medications.models import Medication, MunicipalityStock, Movement


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_admin = user_in_group(request.user, ROLE_ADMIN)
        municipality_name = ""
        if hasattr(request.user, "profile"):
            municipality_name = (request.user.profile.municipality or "").strip()

        if is_admin or not municipality_name:
            materials_total = Medication.objects.count()
            users_total = User.objects.count()
            users_active = User.objects.filter(is_active=True).count()
            movement_qs = Movement.objects.all()
        else:
            materials_total = MunicipalityStock.objects.filter(
                municipality__name__iexact=municipality_name
            ).count()
            users_total = User.objects.count()
            users_active = User.objects.filter(is_active=True).count()
            movement_qs = Movement.objects.filter(municipality__name__iexact=municipality_name)

        if municipality_name:
            movement_qs = movement_qs.filter(municipality__name__iexact=municipality_name)

        now = timezone.now()
        monthly_ingreso = (
            movement_qs.filter(
                type="ingreso", created_at__year=now.year, created_at__month=now.month
            ).aggregate(total=Sum("quantity")).get("total")
            or 0
        )
        monthly_egreso = (
            movement_qs.filter(
                type="egreso", created_at__year=now.year, created_at__month=now.month
            ).aggregate(total=Sum("quantity")).get("total")
            or 0
        )

        return Response(
            {
                "consumption_monthly": float(monthly_ingreso + monthly_egreso),
                "monthly_ingreso": float(monthly_ingreso),
                "monthly_egreso": float(monthly_egreso),
                "materials_total": materials_total,
                "users_total": users_total,
                "users_active": users_active,
                "service_rating": 8.5,
            }
        )


class DashboardChartsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_admin = user_in_group(request.user, ROLE_ADMIN)
        municipality_name = ""
        if hasattr(request.user, "profile"):
            municipality_name = (request.user.profile.municipality or "").strip()

        movement_qs = Movement.objects.all()
        stock_qs = MunicipalityStock.objects.all()
        if not is_admin and municipality_name:
            movement_qs = movement_qs.filter(municipality__name__iexact=municipality_name)
            stock_qs = stock_qs.filter(municipality__name__iexact=municipality_name)

        monthly = (
            movement_qs.annotate(month=TruncMonth("created_at"))
            .values("month", "type")
            .annotate(total=Sum("quantity"))
            .order_by("month")
        )
        monthly_map = {}
        for item in monthly:
            key = item["month"].strftime("%Y-%m") if item["month"] else ""
            if key not in monthly_map:
                monthly_map[key] = {"month": key, "ingreso": 0, "egreso": 0}
            monthly_map[key][item["type"]] = int(item["total"] or 0)

        monthly_series = list(monthly_map.values())

        distribution = (
            stock_qs.values("municipality__name")
            .annotate(total=Sum("stock"))
            .order_by("municipality__name")
        )
        distribution_series = [
            {"municipality": item["municipality__name"], "total": int(item["total"] or 0)}
            for item in distribution
        ]

        trend_series = sorted(distribution_series, key=lambda x: x["total"], reverse=True)[:8]

        return Response(
            {
                "monthly": monthly_series,
                "distribution": distribution_series,
                "trend": trend_series,
            }
        )
