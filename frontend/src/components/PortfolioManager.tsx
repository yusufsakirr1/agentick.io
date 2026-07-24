import { useState } from 'react'
import { Plus, Trash2, ChevronDown } from 'lucide-react'
import { BIST_TICKERS } from '../constants/tickers'
import type { Holding } from '../services/portfolioService'

interface Props {
  holdings: Holding[]
  onAdd: (holding: Holding) => void
  onRemove: (index: number) => void
}

export default function PortfolioManager({ holdings, onAdd, onRemove }: Props) {
  const [showForm, setShowForm] = useState(false)
  const [ticker, setTicker] = useState('')
  const [shares, setShares] = useState('')
  const [avgCost, setAvgCost] = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const usedTickers = new Set(holdings.map(h => h.ticker))
  const availableTickers = BIST_TICKERS.filter(t => !usedTickers.has(t))

  const handleAdd = () => {
    if (!ticker || !shares || !avgCost) return
    onAdd({
      ticker,
      shares: parseFloat(shares),
      avgCost: parseFloat(avgCost),
      addedAt: new Date().toISOString(),
    })
    setTicker('')
    setShares('')
    setAvgCost('')
    setShowForm(false)
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Portföy Sepeti</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 text-xs font-medium text-gray-600 hover:text-gray-900
                     bg-gray-50 hover:bg-gray-100 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          Hisse Ekle
        </button>
      </div>

      {/* Mevcut holdingleri listele */}
      {holdings.length > 0 && (
        <div className="space-y-2 mb-4">
          {holdings.map((h, i) => (
            <div key={`${h.ticker}-${i}`} className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-xl">
              <span className="text-xs font-mono font-bold text-gray-900 bg-white px-2.5 py-1 rounded-lg border border-gray-200">
                {h.ticker}
              </span>
              <span className="text-xs text-gray-500">
                {h.shares} lot
              </span>
              <span className="text-xs text-gray-400">
                x {h.avgCost.toFixed(2)} TL
              </span>
              <div className="flex-1" />
              <span className="text-xs font-medium text-gray-700">
                {(h.shares * h.avgCost).toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} TL
              </span>
              <button
                onClick={() => onRemove(i)}
                className="p-1 text-gray-300 hover:text-red-400 transition-colors cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {holdings.length === 0 && !showForm && (
        <p className="text-xs text-gray-400 text-center py-6">
          Henüz hisse eklenmedi. "Hisse Ekle" ile başlayın.
        </p>
      )}

      {/* Yeni hisse ekleme formu */}
      {showForm && (
        <div className="border border-gray-100 rounded-xl p-4 bg-gray-50/50">
          <div className="grid grid-cols-3 gap-3">
            {/* Ticker dropdown */}
            <div className="relative">
              <label className="block text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Hisse</label>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="w-full flex items-center justify-between px-3 py-2 bg-white border border-gray-200
                           rounded-lg text-sm text-gray-900 hover:border-gray-300 transition-colors cursor-pointer"
              >
                <span className={ticker ? 'font-mono font-semibold' : 'text-gray-400'}>
                  {ticker || 'Seçin'}
                </span>
                <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
              </button>
              {dropdownOpen && (
                <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {availableTickers.map(t => (
                    <button
                      key={t}
                      onClick={() => { setTicker(t); setDropdownOpen(false) }}
                      className="w-full text-left px-3 py-1.5 text-sm font-mono hover:bg-gray-50 transition-colors cursor-pointer"
                    >
                      {t}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Lot */}
            <div>
              <label className="block text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Lot</label>
              <input
                type="number"
                value={shares}
                onChange={e => setShares(e.target.value)}
                placeholder="100"
                min="1"
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm
                           placeholder-gray-300 focus:outline-none focus:border-gray-400 transition-colors"
              />
            </div>

            {/* Ortalama maliyet */}
            <div>
              <label className="block text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Maliyet (TL)</label>
              <input
                type="number"
                value={avgCost}
                onChange={e => setAvgCost(e.target.value)}
                placeholder="250.00"
                min="0"
                step="0.01"
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm
                           placeholder-gray-300 focus:outline-none focus:border-gray-400 transition-colors"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 mt-3">
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors cursor-pointer"
            >
              İptal
            </button>
            <button
              onClick={handleAdd}
              disabled={!ticker || !shares || !avgCost}
              className="px-4 py-1.5 text-xs font-medium text-white bg-gray-900 hover:bg-gray-800
                         disabled:bg-gray-200 disabled:text-gray-400 rounded-lg transition-colors cursor-pointer"
            >
              Ekle
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
