import { useState, useEffect } from 'react'
import AgentLogo from '../components/AgentLogo'
import TickerSelector from '../components/TickerSelector'
import ComparisonTable from '../components/ComparisonTable'
import ComparisonChat from '../components/ComparisonChat'
import { fetchComparisonMetrics, TickerMetrics } from '../api/client'

export default function ComparePage() {
  const [tickers, setTickers] = useState<string[]>(['THYAO', 'TUPRS'])
  const [metrics, setMetrics] = useState<Record<string, TickerMetrics>>({})
  const [metricsLoading, setMetricsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (tickers.length < 2) return

    let cancelled = false
    setMetricsLoading(true)
    setError(null)

    fetchComparisonMetrics(tickers)
      .then(res => {
        if (cancelled) return
        if (res.error) {
          setError(res.error)
          setMetrics({})
        } else {
          setMetrics(res.metrics)
        }
      })
      .catch(e => {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Veri alınamadı')
        setMetrics({})
      })
      .finally(() => {
        if (!cancelled) setMetricsLoading(false)
      })

    return () => { cancelled = true }
  }, [tickers])

  return (
    <>
      {/* Header */}
      <header className="flex-shrink-0 flex items-center gap-3 px-6 py-3 border-b border-gray-100">
        <AgentLogo size={50} />
        <span
          style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
          className="text-[2.4rem] text-gray-900 leading-none tracking-tight -ml-2"
        >
          agentick.io
        </span>
        <span className="text-sm font-medium text-gray-400 ml-2">Karşılaştırma</span>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-5xl mx-auto space-y-6">

          {/* Ticker seçici */}
          <div>
            <p className="text-sm font-medium text-gray-500 mb-2">Karşılaştırılacak 2 hisseyi seçin</p>
            <TickerSelector selected={tickers} onChange={setTickers} />
          </div>

          {/* Hata */}
          {error && (
            <div className="text-sm text-red-500 bg-red-50 px-4 py-2 rounded-lg">
              {error}
            </div>
          )}

          {/* Tablo */}
          <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <ComparisonTable tickers={tickers} metrics={metrics} loading={metricsLoading} />
          </div>

          {/* Divider */}
          <div className="border-t border-gray-200" />

          {/* Soru-cevap */}
          <div>
            <p className="text-sm font-medium text-gray-500 mb-3">Karşılaştırma hakkında soru sorun</p>
            <ComparisonChat tickers={tickers} />
          </div>
        </div>
      </div>
    </>
  )
}
