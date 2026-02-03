from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("medications", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="medication",
            options={"ordering": ["material_name"]},
        ),
        migrations.RemoveField(model_name="medication", name="name"),
        migrations.RemoveField(model_name="medication", name="active_ingredient"),
        migrations.RemoveField(model_name="medication", name="dosage"),
        migrations.RemoveField(model_name="medication", name="form"),
        migrations.RemoveField(model_name="medication", name="stock"),
        migrations.RemoveField(model_name="medication", name="expiration_date"),
        migrations.RemoveField(model_name="medication", name="batch_number"),
        migrations.RemoveField(model_name="medication", name="supplier"),
        migrations.AddField(
            model_name="medication",
            name="category",
            field=models.CharField(max_length=120, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="medication",
            name="code",
            field=models.CharField(max_length=60, unique=True, default="TMP"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="medication",
            name="material_name",
            field=models.CharField(max_length=200, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="medication",
            name="monthly_demand_avg",
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
        migrations.AddField(
            model_name="medication",
            name="physical_stock",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="medication",
            name="months_of_supply",
            field=models.DecimalField(max_digits=6, decimal_places=2, default=0),
        ),
    ]
