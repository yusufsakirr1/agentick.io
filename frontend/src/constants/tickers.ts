export const BIST_TICKERS = [
  'AKBNK', 'AKSEN', 'ARCLK', 'ASELS', 'BIMAS',
  'EKGYO', 'ENKAI', 'EREGL', 'FROTO', 'GARAN',
  'GUBRF', 'HALKB', 'ISCTR', 'KCHOL', 'KONTR',
  'KOZAL', 'KRDMD', 'ODAS',  'PETKM', 'PGSUS',
  'SAHOL', 'SASA',  'SISE',  'TAVHL', 'TCELL',
  'THYAO', 'TOASO', 'TUPRS', 'VAKBN', 'YKBNK',
] as const

export type BistTicker = typeof BIST_TICKERS[number]
