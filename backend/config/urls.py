"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
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
from reports.views import MunicipalityMonthlyReportDownloadView, MunicipalityMonthlyReportView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"medications", MedicationViewSet, basename="medications")
router.register(r"municipalities", MunicipalityViewSet, basename="municipalities")
router.register(r"municipality-stocks", MunicipalityStockViewSet, basename="municipality-stocks")
router.register(r"movements", MovementViewSet, basename="movements")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include(router.urls)),
    path("api/reports/municipality-monthly/", MunicipalityMonthlyReportView.as_view(), name="municipality_monthly"),
    path(
        "api/reports/municipality-monthly/download/",
        MunicipalityMonthlyReportDownloadView.as_view(),
        name="municipality_monthly_download",
    ),
    path("api/dashboard/stats/", DashboardStatsView.as_view(), name="dashboard_stats"),
    path("api/dashboard/charts/", DashboardChartsView.as_view(), name="dashboard_charts"),
    path("api/backup/download/", BackupDownloadView.as_view(), name="backup_download"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="token_logout"),
]
