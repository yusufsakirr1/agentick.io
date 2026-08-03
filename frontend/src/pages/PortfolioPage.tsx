import { useState, useEffect, useCallback, useMemo } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
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
import { describeFirestoreError, withFirestoreTimeout } from '../services/firebaseError'
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
  const [storageError, setStorageError] = useState<string | null>(null)
  const [portfolioLoading, setPortfolioLoading] = useState(true)

  const tickers = holdings.map(h => h.ticker)

  // Firestore'dan portföy yükle.
  // Okuma başarısız olursa holdings'i BOŞALTMIYORUZ — kullanıcıya "portföyün
  // silindi" izlenimi veren eski davranış buydu. Bunun yerine hata gösterilir.
  const loadPortfolio = useCallback(async () => {
    if (!user) return
    setPortfolioLoading(true)
    try {
      setHoldings(await withFirestoreTimeout(getPortfolio(user.uid)))
      setStorageError(null)
    } catch (e) {
      setStorageError(`Portföyünüz yüklenemedi. ${describeFirestoreError(e)}`)
    } finally {
      setPortfolioLoading(false)
    }
  }, [user])

  useEffect(() => {
    loadPortfolio()
  }, [loadPortfolio])

  // Portföy değiştiğinde Firestore'a kaydet.
  // Yazma başarısız olursa kullanıcı uyarılır; aksi halde ekranda duran hisseler
  // kaydedilmiş sanılır ve sonraki girişte kaybolur.
  const saveHoldings = useCallback(async (newHoldings: Holding[]) => {
    if (!user) return
    setHoldings(newHoldings)
    try {
      await withFirestoreTimeout(updateHolding(user.uid, newHoldings))
      setStorageError(null)
    } catch (e) {
      setStorageError(
        `Değişiklik kaydedilemedi — bu sayfadan çıkarsanız kaybolur. ${describeFirestoreError(e)}`,
      )
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

  // Holding içeriğine duyarlı anahtar: lot veya maliyet değişince de metrikler tazelenir
  // (sadece eleman sayısına bakmak, aynı sayıda kalan düzenlemeleri kaçırıyordu)
  const holdingsKey = useMemo(
    () => holdings.map(h => `${h.ticker}:${h.shares}:${h.avgCost}`).join('|'),
    [holdings],
  )

  useEffect(() => {
    if (holdings.length > 0) loadMetrics()
    // loadMetrics bilerek bağımlılığa eklenmedi — holdingsKey değişimi tek tetikleyici
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [holdingsKey])

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

          {/* Kalıcılık hatası — portföy kaydedilemiyor/yüklenemiyorsa sessiz kalma */}
          {storageError && (
            <div className="flex items-start gap-3 text-sm bg-amber-50 border border-amber-200
                            text-amber-900 px-4 py-3 rounded-xl">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" strokeWidth={2} />
              <p className="flex-1 leading-relaxed">{storageError}</p>
              <button
                onClick={loadPortfolio}
                className="flex-shrink-0 flex items-center gap-1 text-xs font-medium
                           px-2.5 py-1 rounded-lg bg-white border border-amber-200
                           hover:bg-amber-100 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3 h-3" />
                Yeniden dene
              </button>
            </div>
          )}

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

          {/* Empty state — yükleme sürerken veya okuma hatası varken gösterme,
              aksi halde "portföyün boş" yanılgısı doğuyor */}
          {!hasData && !portfolioLoading && !storageError && (
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
