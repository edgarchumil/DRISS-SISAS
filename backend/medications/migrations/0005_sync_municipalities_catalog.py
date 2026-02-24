from django.db import migrations


TARGET_NAMES = [
    "DMS Solola",
    "RED Los Encuentros",
    "RED Argueta",
    "RED Concepcion",
    "DMS Panajachel",
    "RED Santa Catarina Palopo",
    "DMS San Andres Semetabaj",
    "DMS San Antonio Palopo",
    "DMS Santa Lucia Utatlan",
    "RED Santa Maria Visitacion",
    "RED San Jose Chacaya",
    "DMS Nahuala",
    "DMS Santa Catrina Ixtahuacan",
    "DMS Santa Clara La Laguna",
    "DMS San Pablo La Laguna",
    "RED Santa Cruz La Laguna",
    "RED Santa Marcos La Laguna",
    "DMS San Pedro La Laguna",
    "DMS San Juan La Laguna",
    "DMS Santiago Atitlan",
    "DMS San Lucas Toliman",
    "DMS Guineales",
    "RED La Ceiba",
    "DMS Xejuyup",
]


def sync_municipalities(apps, schema_editor):
    Municipality = apps.get_model("medications", "Municipality")
    MunicipalityStock = apps.get_model("medications", "MunicipalityStock")
    Movement = apps.get_model("medications", "Movement")

    rename_map = {
        "solola": "DMS Solola",
        "san jose chacaya": "RED San Jose Chacaya",
        "santa maria visitacion": "RED Santa Maria Visitacion",
        "santa lucia utatlan": "DMS Santa Lucia Utatlan",
        "nahuala": "DMS Nahuala",
        "santa catarina ixtahuacan": "DMS Santa Catrina Ixtahuacan",
        "santa clara la laguna": "DMS Santa Clara La Laguna",
        "concepcion": "RED Concepcion",
        "san andres semetabaj": "DMS San Andres Semetabaj",
        "panajachel": "DMS Panajachel",
        "santa catarina palopo": "RED Santa Catarina Palopo",
        "san antonio palopo": "DMS San Antonio Palopo",
        "san lucas toliman": "DMS San Lucas Toliman",
        "santa cruz la laguna": "RED Santa Cruz La Laguna",
        "san pablo la laguna": "DMS San Pablo La Laguna",
        "san marcos la laguna": "RED Santa Marcos La Laguna",
        "san juan la laguna": "DMS San Juan La Laguna",
        "san pedro la laguna": "DMS San Pedro La Laguna",
        "santiago atitlan": "DMS Santiago Atitlan",
    }

    for old_name, new_name in rename_map.items():
        municipality = Municipality.objects.filter(name__iexact=old_name).first()
        if municipality:
            existing_target = Municipality.objects.filter(name__iexact=new_name).first()
            if existing_target and existing_target.pk != municipality.pk:
                duplicate_stocks = MunicipalityStock.objects.filter(municipality=existing_target)
                for stock in duplicate_stocks:
                    base_stock = MunicipalityStock.objects.filter(
                        municipality=municipality,
                        medication=stock.medication,
                    ).first()
                    if base_stock:
                        base_stock.stock += stock.stock
                        base_stock.save(update_fields=["stock", "updated_at"])
                        stock.delete()
                    else:
                        stock.municipality = municipality
                        stock.save(update_fields=["municipality"])

                Movement.objects.filter(municipality=existing_target).update(
                    municipality=municipality
                )
                existing_target.delete()
            municipality.name = new_name
            municipality.save(update_fields=["name"])

    existing = {item.lower(): item for item in Municipality.objects.values_list("name", flat=True)}
    for target in TARGET_NAMES:
        if target.lower() not in existing:
            Municipality.objects.create(name=target)


class Migration(migrations.Migration):
    dependencies = [
        ("medications", "0004_movement"),
    ]

    operations = [
        migrations.RunPython(sync_municipalities, migrations.RunPython.noop),
    ]
