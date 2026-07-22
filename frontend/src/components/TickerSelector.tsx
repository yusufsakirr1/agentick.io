import { useState, useRef, useEffect } from 'react'
import { BIST_TICKERS } from '../constants/tickers'
import { X, Plus } from 'lucide-react'

interface Props {
  selected: string[]
  onChange: (tickers: string[]) => void
}

export default function TickerSelector({ selected, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const available = BIST_TICKERS.filter(t => !selected.includes(t))

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleAdd = (ticker: string) => {
    if (selected.length < 2) {
      onChange([...selected, ticker])
    }
    setOpen(false)
  }

  const handleRemove = (ticker: string) => {
    onChange(selected.filter(t => t !== ticker))
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {selected.map(t => (
        <span
          key={t}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-900 text-white text-sm font-semibold"
        >
          {t}
          <button
            onClick={() => handleRemove(t)}
            className="hover:bg-white/20 rounded-full p-0.5 transition-colors"
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}

      {selected.length < 2 && (
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setOpen(!open)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border-2 border-dashed border-gray-300
                       text-sm font-medium text-gray-500 hover:border-gray-400 hover:text-gray-700 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Ekle
          </button>

          {open && (
            <div className="absolute top-full left-0 mt-1 w-40 bg-white rounded-xl shadow-lg border border-gray-100
                            max-h-60 overflow-y-auto z-50">
              {available.map(t => (
                <button
                  key={t}
                  onClick={() => handleAdd(t)}
                  className="w-full text-left px-3 py-2 text-sm font-mono font-semibold text-gray-700
                             hover:bg-gray-50 transition-colors first:rounded-t-xl last:rounded-b-xl"
                >
                  {t}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
