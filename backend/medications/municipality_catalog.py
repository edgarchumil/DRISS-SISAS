import unicodedata


ORDERED_MUNICIPALITY_CATALOG = [
    {
        "name": "DMS Sololá",
        "aliases": ["DMS Solola", "Solola", "DRISS Sololá"],
    },
    {
        "name": "RED San Juan Argueta",
        "aliases": ["RED Argueta", "San Juan Argueta"],
    },
    {
        "name": "RED Los Encuentros",
        "aliases": ["RED Los Encuentros", "Los Encuentros"],
    },
    {
        "name": "RED Concepción",
        "aliases": ["RED Concepcion", "Concepcion"],
    },
    {
        "name": "DMS Panajachel",
        "aliases": ["DMS Panajachel", "Panajachel"],
    },
    {
        "name": "RED Santa Catarina Palopó",
        "aliases": ["RED Santa Catarina Palopo", "Santa Catarina Palopo"],
    },
    {
        "name": "DMS San Andrés Semetabaj",
        "aliases": ["DMS San Andres Semetabaj", "San Andres Semetabaj"],
    },
    {
        "name": "DMS San Lucas Tolimán",
        "aliases": ["DMS San Lucas Toliman", "San Lucas Toliman"],
    },
    {
        "name": "DMS San Antonio Palopó",
        "aliases": ["DMS San Antonio Palopo", "San Antonio Palopo"],
    },
    {
        "name": "DMS Santiago Atitlán",
        "aliases": ["DMS Santiago Atitlan", "Santiago Atitlan"],
    },
    {
        "name": "DMS Santa Lucía Utatlán",
        "aliases": ["DMS Santa Lucia Utatlan", "Santa Lucia Utatlan"],
    },
    {
        "name": "RED San José Chacayá",
        "aliases": ["RED San Jose Chacaya", "San Jose Chacaya"],
    },
    {
        "name": "RED Santa María Visitación",
        "aliases": ["RED Santa Maria Visitacion", "Santa Maria Visitacion"],
    },
    {
        "name": "DMS Santa Clara La Laguna",
        "aliases": ["DMS Santa Clara La Laguna", "Santa Clara La Laguna"],
    },
    {
        "name": "DMS Nahuala",
        "aliases": ["DMS Nahuala", "Nahuala"],
    },
    {
        "name": "DMS San Pablo La Laguna",
        "aliases": ["DMS San Pablo La Laguna", "San Pablo La Laguna"],
    },
    {
        "name": "RED San Marcos La Laguna",
        "aliases": ["RED Santa Marcos La Laguna", "San Marcos La Laguna"],
    },
    {
        "name": "RED Santa Cruz La Laguna",
        "aliases": ["RED Santa Cruz La Laguna", "Santa Cruz La Laguna"],
    },
    {
        "name": "DMS San Pedro La Laguna",
        "aliases": ["DMS San Pedro La Laguna", "San Pedro La Laguna"],
    },
    {
        "name": "DMS San Juan La Laguna",
        "aliases": ["DMS San Juan La Laguna", "San Juan La Laguna"],
    },
    {
        "name": "DMS Xejuyup",
        "aliases": ["DMS Xejuyup", "Xejuyup"],
    },
    {
        "name": "DMS Guineales",
        "aliases": ["DMS Guineales", "Guineales"],
    },
    {
        "name": "RED La Ceiba",
        "aliases": ["RED La Ceiba", "La Ceiba"],
    },
    {
        "name": "DMS Santa Catarina Ixtahuacán",
        "aliases": [
            "DMS Santa Catrina Ixtahuacan",
            "DMS Santa Catarina Ixtahuacan",
            "Santa Catarina Ixtahuacan",
        ],
    },
]

ORDERED_MUNICIPALITY_NAMES = [item["name"] for item in ORDERED_MUNICIPALITY_CATALOG]


def normalize_municipality_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().strip().split())


DISPLAY_NAME_BY_NORMALIZED_NAME = {}
MUNICIPALITY_ORDER_BY_NORMALIZED_NAME = {}

for position, item in enumerate(ORDERED_MUNICIPALITY_CATALOG, start=1):
    names = [item["name"], *item["aliases"]]
    for name in names:
        normalized_name = normalize_municipality_name(name)
        DISPLAY_NAME_BY_NORMALIZED_NAME[normalized_name] = item["name"]
        MUNICIPALITY_ORDER_BY_NORMALIZED_NAME[normalized_name] = position


def get_display_municipality_name(value: str) -> str:
    normalized_name = normalize_municipality_name(value)
    return DISPLAY_NAME_BY_NORMALIZED_NAME.get(normalized_name, value)
