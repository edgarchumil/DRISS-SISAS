from django.contrib import admin

from medications.models import Medication, Municipality, MunicipalityStock, Movement


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("material_name", "category", "code", "physical_stock", "months_of_supply")
    search_fields = ("material_name", "category", "code")


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(MunicipalityStock)
class MunicipalityStockAdmin(admin.ModelAdmin):
    list_display = ("municipality", "medication", "stock", "updated_at")
    search_fields = ("municipality__name", "medication__material_name", "medication__code")

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("type", "medication", "municipality", "quantity", "user", "created_at")
    search_fields = ("medication__material_name", "municipality__name", "user__username")
