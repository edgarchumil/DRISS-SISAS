from django.db import migrations, models
import django.db.models.deletion


def seed_municipalities(apps, schema_editor):
    Municipality = apps.get_model("medications", "Municipality")
    names = [
        "Solola",
        "San Jose Chacaya",
        "Santa Maria Visitacion",
        "Santa Lucia Utatlan",
        "Nahuala",
        "Santa Catarina Ixtahuacan",
        "Santa Clara La Laguna",
        "Concepcion",
        "San Andres Semetabaj",
        "Panajachel",
        "Santa Catarina Palopo",
        "San Antonio Palopo",
        "San Lucas Toliman",
        "Santa Cruz La Laguna",
        "San Pablo La Laguna",
        "San Marcos La Laguna",
        "San Juan La Laguna",
        "San Pedro La Laguna",
        "Santiago Atitlan",
    ]
    for name in names:
        Municipality.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("medications", "0002_update_material_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="Municipality",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="MunicipalityStock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stock", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "medication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="municipality_stocks",
                        to="medications.medication",
                    ),
                ),
                (
                    "municipality",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stocks",
                        to="medications.municipality",
                    ),
                ),
            ],
            options={"unique_together": {("municipality", "medication")}},
        ),
        migrations.RunPython(seed_municipalities, migrations.RunPython.noop),
    ]
