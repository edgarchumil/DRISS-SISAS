const ORDERED_MUNICIPALITY_CATALOG = [
  { name: 'DMS Sololá', aliases: ['DMS Solola', 'Solola', 'DRISS Sololá'] },
  { name: 'RED San Juan Argueta', aliases: ['RED Argueta', 'San Juan Argueta'] },
  { name: 'RED Los Encuentros', aliases: ['RED Encuentros', 'Los Encuentros'] },
  { name: 'RED Concepción', aliases: ['RED Concepcion', 'Concepcion'] },
  { name: 'DMS Panajachel', aliases: ['Panajachel'] },
  { name: 'RED Santa Catarina Palopó', aliases: ['RED Santa Catarina Palopo', 'Santa Catarina Palopo'] },
  { name: 'DMS San Andrés Semetabaj', aliases: ['DMS San Andres Semetabaj', 'San Andres Semetabaj'] },
  { name: 'DMS San Lucas Tolimán', aliases: ['DMS San Lucas Toliman', 'San Lucas Toliman'] },
  { name: 'DMS San Antonio Palopó', aliases: ['DMS San Antonio Palopo', 'San Antonio Palopo'] },
  { name: 'DMS Santiago Atitlán', aliases: ['DMS Santiago Atitlan', 'Santiago Atitlan'] },
  { name: 'DMS Santa Lucía Utatlán', aliases: ['DMS Santa Lucia Utatlan', 'Santa Lucia Utatlan'] },
  { name: 'RED San José Chacayá', aliases: ['RED San Jose Chacaya', 'San Jose Chacaya'] },
  { name: 'RED Santa María Visitación', aliases: ['RED Santa Maria Visitacion', 'Santa Maria Visitacion'] },
  { name: 'DMS Santa Clara La Laguna', aliases: ['Santa Clara La Laguna'] },
  { name: 'DMS Nahuala', aliases: ['Nahuala'] },
  { name: 'DMS San Pablo La Laguna', aliases: ['San Pablo La Laguna'] },
  { name: 'RED San Marcos La Laguna', aliases: ['RED Santa Marcos La Laguna', 'San Marcos La Laguna'] },
  { name: 'RED Santa Cruz La Laguna', aliases: ['Santa Cruz La Laguna'] },
  { name: 'DMS San Pedro La Laguna', aliases: ['San Pedro La Laguna'] },
  { name: 'DMS San Juan La Laguna', aliases: ['San Juan La Laguna'] },
  { name: 'DMS Xejuyup', aliases: ['Xejuyup'] },
  { name: 'DMS Guineales', aliases: ['Guineales'] },
  { name: 'RED La Ceiba', aliases: ['La Ceiba'] },
  {
    name: 'DMS Santa Catarina Ixtahuacán',
    aliases: ['DMS Santa Catrina Ixtahuacan', 'DMS Santa Catarina Ixtahuacan', 'Santa Catarina Ixtahuacan'],
  },
];

export function normalizeMunicipalityName(value: string) {
  return (value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ');
}

const DISPLAY_NAME_BY_NORMALIZED_NAME = new Map<string, string>();
for (const item of ORDERED_MUNICIPALITY_CATALOG) {
  for (const name of [item.name, ...item.aliases]) {
    DISPLAY_NAME_BY_NORMALIZED_NAME.set(normalizeMunicipalityName(name), item.name);
  }
}

export function getDisplayMunicipalityName(value: string) {
  const normalized = normalizeMunicipalityName(value);
  return DISPLAY_NAME_BY_NORMALIZED_NAME.get(normalized) ?? value.trim();
}

export function municipalityNamesMatch(left: string, right: string) {
  return normalizeMunicipalityName(getDisplayMunicipalityName(left)) ===
    normalizeMunicipalityName(getDisplayMunicipalityName(right));
}
