from django.db import migrations


def add_driss_solola(apps, schema_editor):
    Municipality = apps.get_model("medications", "Municipality")
    Municipality.objects.get_or_create(name="DRISS Sololá")


class Migration(migrations.Migration):
    dependencies = [
        ("medications", "0005_sync_municipalities_catalog"),
    ]

    operations = [
        migrations.RunPython(add_driss_solola, migrations.RunPython.noop),
    ]
