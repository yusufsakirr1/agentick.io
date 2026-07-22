import { TickerMetrics } from '../api/client'

interface Props {
  tickers: string[]
  metrics: Record<string, TickerMetrics>
  loading: boolean
}

function formatNumber(value: number | null | undefined): string {
  if (value == null) return '-'

  const abs = Math.abs(value)
  if (abs >= 1e12) return `${(value / 1e12).toFixed(1)} T TL`
  if (abs >= 1e9) return `${(value / 1e9).toFixed(0)} Mrd TL`
  if (abs >= 1e6) return `${(value / 1e6).toFixed(0)} Mn TL`
  if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`
  return value.toFixed(2)
}

function formatRatio(value: number | null | undefined, suffix = ''): string {
  if (value == null) return '-'
  return `${value.toFixed(2)}${suffix}`
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) return '-'
  return `%${value.toFixed(1)}`
}

function formatPrice(value: number | null | undefined): string {
  if (value == null) return '-'
  return `${value.toFixed(2)} TL`
}

const METRIC_ROWS: Array<{ label: string; key: string; format: (v: number | null | undefined) => string }> = [
  { label: 'Fiyat', key: 'current_price', format: formatPrice },
  { label: 'Piyasa Değeri', key: 'market_cap', format: formatNumber },
  { label: 'F/K', key: 'pe_ratio', format: v => formatRatio(v) },
  { label: 'PD/DD', key: 'pb_ratio', format: v => formatRatio(v) },
  { label: 'Net Marj', key: 'net_margin', format: formatPercent },
  { label: 'ROE', key: 'roe', format: formatPercent },
  { label: 'ROA', key: 'roa', format: formatPercent },
  { label: 'Borç/Özkaynak', key: 'debt_to_equity', format: v => formatRatio(v) },
  { label: 'Temettü Verimi', key: 'dividend_yield', format: formatPercent },
  { label: 'Gelir', key: 'revenue', format: formatNumber },
  { label: 'Net Kâr', key: 'net_income', format: formatNumber },
  { label: 'FAVÖK', key: 'ebitda', format: formatNumber },
]

function SkeletonRow() {
  return (
    <tr>
      <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-24 animate-pulse" /></td>
      <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-20 animate-pulse" /></td>
      <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded w-20 animate-pulse" /></td>
    </tr>
  )
}

export default function ComparisonTable({ tickers, metrics, loading }: Props) {
  if (loading) {
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Metrik</th>
              {tickers.map(t => (
                <th key={t} className="text-right px-4 py-3 font-semibold text-gray-900">{t}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)}
          </tbody>
        </table>
      </div>
    )
  }

  if (Object.keys(metrics).length === 0) return null

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left px-4 py-3 text-gray-500 font-medium">Metrik</th>
            {tickers.map(t => (
              <th key={t} className="text-right px-4 py-3 font-semibold text-gray-900 font-mono">{t}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {METRIC_ROWS.map(row => (
            <tr key={row.key} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-gray-600 font-medium">{row.label}</td>
              {tickers.map(t => {
                const m = metrics[t]
                const val = m ? (m as unknown as Record<string, number | null>)[row.key] : null
                return (
                  <td key={t} className="px-4 py-3 text-right font-mono text-gray-900">
                    {row.format(val)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
