const BASE_URL = '/api'

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

export async function uploadPDF(ticker: string, file: File, sync = false): Promise<UploadResult> {
  const form = new FormData()
  form.append('ticker', ticker)
  form.append('file', file)

  const endpoint = sync ? `${BASE_URL}/upload/sync` : `${BASE_URL}/upload`
  const res = await fetch(endpoint, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Yükleme hatası')
  }
  return res.json()
}

export async function fetchFinancialData(ticker: string): Promise<{ status: string; ticker: string }> {
  const res = await fetch(`${BASE_URL}/fetch-data`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
  const res = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, ticker, conversation_history: conversationHistory }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Sorgu hatası')
  }
  return res.json()
}
