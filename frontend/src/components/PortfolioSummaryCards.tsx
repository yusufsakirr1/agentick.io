import { TrendingUp, TrendingDown, Banknote, Target, BarChart3, Percent, Coins } from 'lucide-react'
import type { PortfolioSummary } from '../api/client'

interface Props {
  summary: PortfolioSummary | null
  loading: boolean
}

function formatCurrency(v: number): string {
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(1)}M TL`
  return v.toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' TL'
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      <div className="h-3 w-20 bg-gray-100 rounded animate-pulse mb-3" />
      <div className="h-7 w-28 bg-gray-100 rounded animate-pulse" />
    </div>
  )
}

export default function PortfolioSummaryCards({ summary, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  if (!summary) return null

  const isProfit = summary.totalProfitLoss >= 0

  const cards = [
    {
      label: 'Toplam Değer',
      value: formatCurrency(summary.totalValue),
      icon: Banknote,
      color: 'text-gray-900',
      bg: 'bg-gray-50',
    },
    {
      label: 'Toplam Maliyet',
      value: formatCurrency(summary.totalCost),
      icon: Target,
      color: 'text-gray-500',
      bg: 'bg-gray-50',
    },
    {
      label: 'Kâr / Zarar',
      value: `${isProfit ? '+' : ''}${formatCurrency(summary.totalProfitLoss)}`,
      icon: isProfit ? TrendingUp : TrendingDown,
      color: isProfit ? 'text-emerald-600' : 'text-red-500',
      bg: isProfit ? 'bg-emerald-50' : 'bg-red-50',
    },
    {
      label: 'K/Z Oranı',
      value: `${isProfit ? '+' : ''}%${summary.totalProfitLossPct.toFixed(1)}`,
      icon: Percent,
      color: isProfit ? 'text-emerald-600' : 'text-red-500',
      bg: isProfit ? 'bg-emerald-50' : 'bg-red-50',
    },
    {
      label: 'Ağırlıklı F/K',
      value: summary.weightedPE != null ? summary.weightedPE.toFixed(1) : '-',
      icon: BarChart3,
      color: 'text-gray-900',
      bg: 'bg-gray-50',
    },
    {
      label: 'Ağırlıklı Temettü',
      value: summary.weightedDividendYield != null ? `%${summary.weightedDividendYield.toFixed(1)}` : '-',
      icon: Coins,
      color: 'text-gray-900',
      bg: 'bg-gray-50',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
      {cards.map(c => {
        const Icon = c.icon
        return (
          <div key={c.label} className={`${c.bg} rounded-2xl p-5 border border-gray-100/80`}>
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-4 h-4 ${c.color} opacity-60`} strokeWidth={1.8} />
              <span className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">{c.label}</span>
            </div>
            <p className={`text-xl font-bold ${c.color} tracking-tight`}>{c.value}</p>
          </div>
        )
      })}
    </div>
  )
}
