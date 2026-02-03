from rest_framework import serializers

from medications.models import Medication, Municipality, MunicipalityStock, Movement


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = [
            "id",
            "category",
            "code",
            "material_name",
            "monthly_demand_avg",
            "physical_stock",
            "months_of_supply",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = ["id", "name"]


class MunicipalityStockSerializer(serializers.ModelSerializer):
    municipality_name = serializers.CharField(source="municipality.name", read_only=True)
    medication_name = serializers.CharField(source="medication.material_name", read_only=True)
    stock = serializers.IntegerField(min_value=0, required=False)

    class Meta:
        model = MunicipalityStock
        fields = ["id", "municipality", "municipality_name", "medication", "medication_name", "stock", "updated_at"]
        read_only_fields = ["id", "updated_at", "municipality_name", "medication_name"]


class MovementSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.material_name", read_only=True)
    municipality_name = serializers.CharField(source="municipality.name", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Movement
        fields = [
            "id",
            "type",
            "medication",
            "medication_name",
            "municipality",
            "municipality_name",
            "user",
            "user_name",
            "quantity",
            "notes",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "medication_name",
            "municipality_name",
            "user",
            "user_name",
            "created_at",
        ]
