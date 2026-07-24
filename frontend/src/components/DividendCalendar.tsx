import { Calendar } from 'lucide-react'
import type { DividendEntry } from '../api/client'

interface Props {
  dividends: DividendEntry[]
  loading: boolean
}

const MONTHS = [
  'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık',
]

function formatDateTR(dateStr: string): string {
  if (!dateStr || dateStr.length < 10) return dateStr
  const [y, m, d] = dateStr.slice(0, 10).split('-')
  const monthIdx = parseInt(m, 10) - 1
  const month = MONTHS[monthIdx] ?? m
  return `${parseInt(d, 10)} ${month} ${y}`
}

export default function DividendCalendar({ dividends, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 p-5">
        <div className="h-4 w-32 bg-gray-100 rounded animate-pulse mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-8 bg-gray-50 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Calendar className="w-4 h-4 text-gray-400" strokeWidth={1.8} />
        <h3 className="text-sm font-semibold text-gray-900">Temettü Takvimi</h3>
      </div>

      {dividends.length === 0 ? (
        <p className="text-xs text-gray-400 text-center py-4">Temettü verisi bulunamadı</p>
      ) : (
        <div className="space-y-2">
          {dividends.map((d, i) => (
            <div key={`${d.ticker}-${d.ex_date}-${i}`} className="flex items-center gap-3 px-3 py-2.5 bg-gray-50 rounded-xl">
              <span className="text-[11px] text-gray-500 w-28 flex-shrink-0">
                {formatDateTR(d.ex_date)}
              </span>
              <span className="text-xs font-mono font-bold text-gray-900 bg-white px-2 py-0.5 rounded-lg border border-gray-200">
                {d.ticker}
              </span>
              <div className="flex-1" />
              <div className="text-right">
                <span className="text-xs font-mono font-semibold text-emerald-600">
                  {d.amount.toFixed(2)} TL
                </span>
                <span className="text-[10px] text-gray-400 ml-1">/hisse</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
