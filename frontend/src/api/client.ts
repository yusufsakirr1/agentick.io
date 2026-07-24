import { auth } from '../config/firebase'

const BASE_URL = '/api'

async function getAuthHeaders(): Promise<Record<string, string>> {
  const user = auth.currentUser
  if (!user) return {}
  const token = await user.getIdToken()
  return { Authorization: `Bearer ${token}` }
}

export interface UploadResult {
  status: string
  message?: string
  filename?: string
  tables?: number
  chunks_indexed?: boolean
  yfinance_updated?: boolean
  error?: string
}

export interface AskResult {
  answer: string
  ticker: string
  sub_tasks: Array<{ query: string; type: string }>
  retrieved_count: number
  retry_count: number
  critic_feedback: string
  error?: string
}

export interface TickerMetrics {
  ticker: string
  current_price: number | null
  market_cap: number | null
  pe_ratio: number | null
  pb_ratio: number | null
  net_margin: number | null
  roe: number | null
  roa: number | null
  debt_to_equity: number | null
  dividend_yield: number | null
  revenue: number | null
  net_income: number | null
  ebitda: number | null
  total_assets: number | null
  total_equity: number | null
  total_debt: number | null
  ratios_date: string | null
  income_date: string | null
}

export interface ComparisonMetrics {
  tickers: string[]
  metrics: Record<string, TickerMetrics>
  error?: string
}

export interface CompareAskResult {
  answer: string
  tickers: string[]
  sub_tasks: Array<{ query: string; type: string }>
  retrieved_count: number
  retry_count: number
  critic_feedback: string
  error?: string
}

export async function uploadPDF(ticker: string, file: File, sync = false): Promise<UploadResult> {
  const form = new FormData()
  form.append('ticker', ticker)
  form.append('file', file)

  const authHeaders = await getAuthHeaders()
  const endpoint = sync ? `${BASE_URL}/upload/sync` : `${BASE_URL}/upload`
  const res = await fetch(endpoint, { method: 'POST', headers: authHeaders, body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Yükleme hatası')
  }
  return res.json()
}

export async function fetchFinancialData(ticker: string): Promise<{ status: string; ticker: string }> {
  const authHeaders = await getAuthHeaders()
  const res = await fetch(`${BASE_URL}/fetch-data`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify({ ticker }),
  })
  if (!res.ok) throw new Error('Veri çekme hatası')
  return res.json()
}

export async function askQuestion(
  question: string,
  ticker: string,
  conversationHistory: Array<{ role: string; content: string }> = [],
): Promise<AskResult> {
  const authHeaders = await getAuthHeaders()
  const res = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify({ question, ticker, conversation_history: conversationHistory }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Sorgu hatası')
  }
  return res.json()
}

export async function fetchComparisonMetrics(tickers: string[]): Promise<ComparisonMetrics> {
  const authHeaders = await getAuthHeaders()
  const params = tickers.join(',')
  const res = await fetch(`${BASE_URL}/compare/metrics?tickers=${encodeURIComponent(params)}`, {
    headers: authHeaders,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Karşılaştırma verisi alınamadı')
  }
  return res.json()
}

// ── Portfolio Types ──

export interface PortfolioHoldingInput {
  ticker: string
  shares: number
  avgCost: number
}

export interface PortfolioHoldingMetrics {
  ticker: string
  shares: number
  avgCost: number
  currentPrice: number
  marketValue: number
  costBasis: number
  profitLoss: number
  profitLossPct: number
  weight: number
  sector: string
  pe_ratio: number | null
  dividend_yield: number | null
  net_margin: number | null
}

export interface PortfolioSummary {
  totalValue: number
  totalCost: number
  totalProfitLoss: number
  totalProfitLossPct: number
  weightedPE: number | null
  weightedDividendYield: number | null
  weightedNetMargin: number | null
}

export interface SectorAllocation {
  sector: string
  weight: number
  tickers: string[]
}

export interface DividendEntry {
  ticker: string
  ex_date: string
  amount: number
}

export interface PortfolioMetricsResult {
  holdings: PortfolioHoldingMetrics[]
  summary: PortfolioSummary
  sectorAllocation: SectorAllocation[]
  warnings: string[]
  dividends: DividendEntry[]
  error?: string
}

export interface NewsArticle {
  ticker: string
  title: string
  summary: string
  link: string
  source: string
  published_at: string
}

export interface PortfolioNewsResult {
  tickers: string[]
  count: number
  articles: NewsArticle[]
  error?: string
}

// ── Portfolio API Functions ──

export async function fetchPortfolioMetrics(holdings: PortfolioHoldingInput[]): Promise<PortfolioMetricsResult> {
  const authHeaders = await getAuthHeaders()
  const res = await fetch(`${BASE_URL}/portfolio/metrics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify({ holdings }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Portföy metrik hatası')
  }
  return res.json()
}

export async function askPortfolioQuestion(
  question: string,
  tickers: string[],
  conversationHistory: Array<{ role: string; content: string }> = [],
): Promise<CompareAskResult> {
  const authHeaders = await getAuthHeaders()
  const res = await fetch(`${BASE_URL}/portfolio/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify({ question, tickers, conversation_history: conversationHistory }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Portföy sorgu hatası')
  }
  return res.json()
}

export async function fetchPortfolioNews(tickers: string[]): Promise<PortfolioNewsResult> {
  const authHeaders = await getAuthHeaders()
  const res = await fetch(`${BASE_URL}/portfolio/news`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify({ tickers }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Portföy haber hatası')
  }
  return res.json()
}

export async function askCompareQuestion(
  question: string,
  tickers: string[],
  conversationHistory: Array<{ role: string; content: string }> = [],
): Promise<CompareAskResult> {
  const authHeaders = await getAuthHeaders()
  const res = await fetch(`${BASE_URL}/compare/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify({ question, tickers, conversation_history: conversationHistory }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Karşılaştırma sorgu hatası')
  }
  return res.json()
}
