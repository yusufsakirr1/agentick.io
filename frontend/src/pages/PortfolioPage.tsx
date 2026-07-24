import { useState, useEffect, useCallback } from 'react'
import AgentLogo from '../components/AgentLogo'
import PortfolioManager from '../components/PortfolioManager'
import PortfolioSummaryCards from '../components/PortfolioSummaryCards'
import SectorChart from '../components/SectorChart'
import ConcentrationWarnings from '../components/ConcentrationWarnings'
import PortfolioHoldingsTable from '../components/PortfolioHoldingsTable'
import DividendCalendar from '../components/DividendCalendar'
import PortfolioNews from '../components/PortfolioNews'
import PortfolioChat from '../components/PortfolioChat'
import { useAuth } from '../contexts/AuthContext'
import {
  getPortfolio,
  updateHolding,
  type Holding,
} from '../services/portfolioService'
import {
  fetchPortfolioMetrics,
  type PortfolioSummary,
  type PortfolioHoldingMetrics,
  type SectorAllocation,
  type DividendEntry,
} from '../api/client'

export default function PortfolioPage() {
  const { user } = useAuth()
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [metricsLoading, setMetricsLoading] = useState(false)
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [holdingMetrics, setHoldingMetrics] = useState<PortfolioHoldingMetrics[]>([])
  const [sectors, setSectors] = useState<SectorAllocation[]>([])
  const [warnings, setWarnings] = useState<string[]>([])
  const [dividends, setDividends] = useState<DividendEntry[]>([])
  const [error, setError] = useState<string | null>(null)

  const tickers = holdings.map(h => h.ticker)

  // Firestore'dan portföy yükle
  useEffect(() => {
    if (!user) return
    getPortfolio(user.uid)
      .then(setHoldings)
      .catch(() => setHoldings([]))
  }, [user])

  // Portföy değiştiğinde Firestore'a kaydet
  const saveHoldings = useCallback(async (newHoldings: Holding[]) => {
    if (!user) return
    setHoldings(newHoldings)
    try {
      await updateHolding(user.uid, newHoldings)
    } catch {
      // silently fail — local state is source of truth during session
    }
  }, [user])

  // Metrikleri çek
  const loadMetrics = useCallback(async () => {
    if (!holdings.length) {
      setSummary(null)
      setHoldingMetrics([])
      setSectors([])
      setWarnings([])
      setDividends([])
      return
    }

    setMetricsLoading(true)
    setError(null)

    try {
      const res = await fetchPortfolioMetrics(
        holdings.map(h => ({ ticker: h.ticker, shares: h.shares, avgCost: h.avgCost }))
      )
      if (res.error) {
        setError(res.error)
      } else {
        setSummary(res.summary)
        setHoldingMetrics(res.holdings)
        setSectors(res.sectorAllocation)
        setWarnings(res.warnings)
        setDividends(res.dividends)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Metrik verisi alınamadı')
    } finally {
      setMetricsLoading(false)
    }
  }, [holdings])

  useEffect(() => {
    if (holdings.length > 0) loadMetrics()
  }, [holdings.length]) // sadece eleman sayısı değiştiğinde

  const handleAdd = (holding: Holding) => {
    saveHoldings([...holdings, holding])
  }

  const handleRemove = (index: number) => {
    const updated = holdings.filter((_, i) => i !== index)
    saveHoldings(updated)
  }

  const hasData = holdings.length > 0

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
        <span className="text-sm font-medium text-gray-400 ml-2">Portföy</span>
      </header>

      {/* Dashboard Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-6xl mx-auto space-y-5">

          {/* Row 1: Portföy Sepeti */}
          <PortfolioManager
            holdings={holdings}
            onAdd={handleAdd}
            onRemove={handleRemove}
          />

          {/* Hata */}
          {error && (
            <div className="text-sm text-red-500 bg-red-50 px-4 py-2 rounded-lg">{error}</div>
          )}

          {/* Analiz butonu */}
          {hasData && (
            <button
              onClick={loadMetrics}
              disabled={metricsLoading}
              className="w-full py-3 text-sm font-medium text-white bg-gray-900 hover:bg-gray-800
                         disabled:bg-gray-300 rounded-xl transition-colors cursor-pointer flex items-center justify-center gap-2"
            >
              {metricsLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  Veriler yükleniyor...
                </>
              ) : (
                'Portföyü Analiz Et'
              )}
            </button>
          )}

          {/* Dashboard Grid */}
          {hasData && (summary || metricsLoading) && (
            <>
              {/* Özet Kartlar */}
              <PortfolioSummaryCards summary={summary} loading={metricsLoading} />

              {/* Uyarılar */}
              <ConcentrationWarnings warnings={warnings} />

              {/* 2-kolon grid: Sektör + Temettü */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <SectorChart sectors={sectors} loading={metricsLoading} />
                <DividendCalendar dividends={dividends} loading={metricsLoading} />
              </div>

              {/* Holdings Tablosu */}
              <PortfolioHoldingsTable holdings={holdingMetrics} loading={metricsLoading} />

              {/* 2-kolon grid: Haberler + Chat */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <PortfolioNews tickers={tickers} />
                <PortfolioChat tickers={tickers} />
              </div>
            </>
          )}

          {/* Empty state */}
          {!hasData && (
            <div className="text-center py-16">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-2xl flex items-center justify-center">
                <AgentLogo size={40} color="#9ca3af" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Portföyünüzü Oluşturun</h2>
              <p className="text-sm text-gray-400 max-w-md mx-auto">
                BIST hisselerinizi ekleyin, AI destekli analiz dashboard'u ile portföyünüzü
                derinlemesine inceleyin.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
