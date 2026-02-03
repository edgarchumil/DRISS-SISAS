from django.contrib.auth.models import User
from django.db import models


class Medication(models.Model):
    category = models.CharField(max_length=120)
    code = models.CharField(max_length=60, unique=True)
    material_name = models.CharField(max_length=200)
    monthly_demand_avg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    physical_stock = models.PositiveIntegerField(default=0)
    months_of_supply = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["material_name"]

    def __str__(self):
        return f"{self.material_name} ({self.code})"

class Municipality(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MunicipalityStock(models.Model):
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, related_name="stocks"
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="municipality_stocks"
    )
    stock = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("municipality", "medication")

    def __str__(self):
        return f"{self.municipality} - {self.medication} ({self.stock})"


class Movement(models.Model):
    TYPE_CHOICES = [
        ("ingreso", "Ingreso"),
        ("egreso", "Egreso"),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name="movements"
    )
    municipality = models.ForeignKey(
        Municipality, on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} - {self.medication} ({self.quantity})"
