import type { PortfolioHoldingMetrics } from '../api/client'

interface Props {
  holdings: PortfolioHoldingMetrics[]
  loading: boolean
}

function fmt(v: number, decimals = 2): string {
  return v.toLocaleString('tr-TR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

function fmtBig(v: number): string {
  const abs = Math.abs(v)
  if (abs >= 1e6) return `${(v / 1e6).toFixed(1)}M`
  if (abs >= 1e3) return `${(v / 1e3).toFixed(0)}K`
  return fmt(v, 0)
}

function SkeletonRows() {
  return (
    <>
      {[1, 2, 3].map(i => (
        <tr key={i}>
          {Array.from({ length: 9 }).map((_, j) => (
            <td key={j} className="px-3 py-3">
              <div className="h-4 bg-gray-100 rounded animate-pulse w-16" />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}

export default function PortfolioHoldingsTable({ holdings, loading }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-50">
        <h3 className="text-sm font-semibold text-gray-900">Holding Detayları</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left px-3 py-3 font-medium text-gray-400">Hisse</th>
              <th className="text-right px-3 py-3 font-medium text-gray-400">Lot</th>
              <th className="text-right px-3 py-3 font-medium text-gray-400">Maliyet</th>
              <th className="text-right px-3 py-3 font-medium text-gray-400">Fiyat</th>
              <th className="text-right px-3 py-3 font-medium text-gray-400">Değer</th>
              <th className="text-right px-3 py-3 font-medium text-gray-400">K/Z</th>
              <th className="text-right px-3 py-3 font-medium text-gray-400">K/Z%</th>
              <th className="text-right px-3 py-3 font-medium text-gray-400">Ağırlık</th>
              <th className="text-left px-3 py-3 font-medium text-gray-400">Sektör</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonRows />
            ) : (
              holdings.map(h => {
                const isProfit = h.profitLoss >= 0
                return (
                  <tr key={h.ticker} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="px-3 py-3">
                      <span className="font-mono font-bold text-gray-900">{h.ticker}</span>
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-gray-700">{h.shares}</td>
                    <td className="px-3 py-3 text-right font-mono text-gray-500">{fmt(h.avgCost)} TL</td>
                    <td className="px-3 py-3 text-right font-mono text-gray-900">{fmt(h.currentPrice)} TL</td>
                    <td className="px-3 py-3 text-right font-mono text-gray-900 font-medium">{fmtBig(h.marketValue)} TL</td>
                    <td className={`px-3 py-3 text-right font-mono font-medium ${isProfit ? 'text-emerald-600' : 'text-red-500'}`}>
                      {isProfit ? '+' : ''}{fmtBig(h.profitLoss)} TL
                    </td>
                    <td className={`px-3 py-3 text-right font-mono font-medium ${isProfit ? 'text-emerald-600' : 'text-red-500'}`}>
                      {isProfit ? '+' : ''}{h.profitLossPct.toFixed(1)}%
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-gray-700">{h.weight.toFixed(1)}%</td>
                    <td className="px-3 py-3 text-left">
                      <span className="text-[10px] text-gray-500 bg-gray-50 px-2 py-0.5 rounded-full">
                        {h.sector}
                      </span>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {!loading && holdings.length === 0 && (
        <div className="text-center py-8 text-xs text-gray-400">Holding verisi yok</div>
      )}
    </div>
  )
}
