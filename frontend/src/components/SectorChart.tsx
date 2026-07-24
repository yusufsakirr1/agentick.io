import type { SectorAllocation } from '../api/client'

interface Props {
  sectors: SectorAllocation[]
  loading: boolean
}

const COLORS = [
  'bg-gray-900',
  'bg-blue-500',
  'bg-emerald-500',
  'bg-amber-500',
  'bg-purple-500',
  'bg-rose-500',
  'bg-cyan-500',
  'bg-orange-500',
]

export default function SectorChart({ sectors, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 p-5">
        <div className="h-4 w-32 bg-gray-100 rounded animate-pulse mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-6 bg-gray-50 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (!sectors.length) return null

  const maxWeight = Math.max(...sectors.map(s => s.weight), 1)

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Sektör Dağılımı</h3>

      <div className="space-y-3">
        {sectors.map((s, i) => (
          <div key={s.sector}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${COLORS[i % COLORS.length]}`} />
                <span className="text-xs font-medium text-gray-700">{s.sector}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  {s.tickers.map(t => (
                    <span key={t} className="text-[10px] font-mono text-gray-400">{t}</span>
                  ))}
                </div>
                <span className="text-xs font-bold text-gray-900 w-12 text-right">%{s.weight.toFixed(0)}</span>
              </div>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${COLORS[i % COLORS.length]} transition-all duration-700 ease-out`}
                style={{ width: `${(s.weight / maxWeight) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
