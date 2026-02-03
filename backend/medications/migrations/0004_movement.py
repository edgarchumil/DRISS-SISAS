from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("medications", "0003_add_municipality_stock"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Movement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("ingreso", "Ingreso"), ("egreso", "Egreso")], max_length=10)),
                ("quantity", models.PositiveIntegerField()),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "medication",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movements", to="medications.medication"),
                ),
                (
                    "municipality",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="medications.municipality"),
                ),
                (
                    "user",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="auth.user"),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
