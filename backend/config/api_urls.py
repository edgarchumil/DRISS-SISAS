from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import LogoutView, UserViewSet
from backup.views import BackupDownloadView
from dashboard.views import DashboardChartsView, DashboardStatsView
from medications.views import (
    MedicationViewSet,
    MovementViewSet,
    MunicipalityStockViewSet,
    MunicipalityViewSet,
)
from reports.views import (
    AllMunicipalitiesMonthlyReportDownloadView,
    MunicipalityMonthlyReportDownloadView,
    MunicipalityMonthlyReportView,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"medications", MedicationViewSet, basename="medications")
router.register(r"municipalities", MunicipalityViewSet, basename="municipalities")
router.register(r"municipality-stocks", MunicipalityStockViewSet, basename="municipality-stocks")
router.register(r"movements", MovementViewSet, basename="movements")

urlpatterns = [
    path("reports/municipality-monthly/", MunicipalityMonthlyReportView.as_view(), name="municipality_monthly"),
    path(
        "reports/municipality-monthly/download/",
        MunicipalityMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_download",
    ),
    path(
        "reports/municipality-monthly/all/download/",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_all_download",
    ),
    path(
        "reports/municipality-monthly/consolidated/download/",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_consolidated_download",
    ),
    path(
        "reports/municipality-monthly/consolidated/download",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_consolidated_download_noslash",
    ),
    path(
        "reports/municipality-monthly/consolidated/",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_consolidated_alias",
    ),
    path(
        "reports/municipality-monthly/consolidated",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_consolidated_alias_noslash",
    ),
    path(
        "reports/municipality-monthly/all/download",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_all_download_noslash",
    ),
    path(
        "reports/municipality-monthly/all/",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_all_alias",
    ),
    path(
        "reports/municipality-monthly/all",
        AllMunicipalitiesMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_all_alias_noslash",
    ),
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard_stats"),
    path("dashboard/charts/", DashboardChartsView.as_view(), name="dashboard_charts"),
    path("backup/download/", BackupDownloadView.as_view(), name="backup_download"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="token_logout"),
]

urlpatterns += router.urls
