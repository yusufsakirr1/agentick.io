import React, { useRef, useState, useEffect } from 'react'
import { uploadPDF, fetchFinancialData } from '../api/client'
import { RefreshCw } from 'lucide-react'
import { BIST_TICKERS } from '../constants/tickers'

type UploadStatus = 'idle' | 'uploading' | 'done' | 'error'

interface Props {
  onSend: (question: string, ticker: string) => void
  loading: boolean
  ticker: string
  onTickerChange: (t: string) => void
  initialQuestion?: string
}

export default function ChatInput({ onSend, loading, ticker, onTickerChange, initialQuestion }: Props) {
  const [text, setText] = useState(initialQuestion ?? '')
  const [file, setFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle')
  const [fetchingData, setFetchingData] = useState(false)
  const [fetchMsg, setFetchMsg] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const textRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (initialQuestion) { setText(initialQuestion); textRef.current?.focus() }
  }, [initialQuestion])

  const handleFile = async (f: File) => {
    if (!f.name.endsWith('.pdf')) return
    setFile(f)
    setUploadStatus('uploading')
    try {
      await uploadPDF(ticker, f, true)
      setUploadStatus('done')
    } catch {
      setUploadStatus('error')
    }
  }

  const handleFetchData = async () => {
    if (fetchingData) return
    setFetchingData(true)
    setFetchMsg('')
    try {
      await fetchFinancialData(ticker)
      setFetchMsg('Veriler güncellendi')
    } catch {
      setFetchMsg('Hata')
    } finally {
      setFetchingData(false)
      setTimeout(() => setFetchMsg(''), 3000)
    }
  }

  const handleSend = () => {
    const q = text.trim()
    if (!q || loading || uploadStatus === 'uploading') return
    onSend(q, ticker)
    setText('')
    setFile(null)
    setUploadStatus('idle')
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const canSend = text.trim().length > 0 && !loading && uploadStatus !== 'uploading'

  const attachColor = {
    idle: 'text-gray-400 hover:text-gray-600',
    uploading: 'text-blue-400',
    done: 'text-green-500',
    error: 'text-red-400',
  }[uploadStatus]

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="flex items-center gap-2 bg-white rounded-full px-4 py-3
                      shadow-[0_2px_20px_rgba(0,0,0,0.09)] ring-1 ring-gray-100">

        {/* Paperclip */}
        <button
          onClick={() => fileRef.current?.click()}
          title={file ? `${file.name} (${uploadStatus})` : 'PDF yükle'}
          className={`flex-shrink-0 p-1 rounded-lg transition-colors ${attachColor}`}
        >
          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
          </svg>
        </button>
        <input ref={fileRef} type="file" accept=".pdf" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); e.target.value = '' }} />

        {/* Divider */}
        <div className="w-px h-4 bg-gray-200 flex-shrink-0" />

        {/* Ticker */}
        <div className="relative flex-shrink-0">
          <select
            value={ticker}
            onChange={(e) => onTickerChange(e.target.value)}
            className="appearance-none bg-transparent pl-1 pr-5 py-0.5 text-sm font-semibold
                       text-gray-700 cursor-pointer focus:outline-none"
          >
            {BIST_TICKERS.map(t => <option key={t}>{t}</option>)}
          </select>
          <svg className="pointer-events-none absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400"
               fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/>
          </svg>
        </div>

        {/* Fetch data button */}
        <button
          onClick={handleFetchData}
          disabled={fetchingData}
          title="yfinance verilerini güncelle"
          className="flex-shrink-0 p-1 rounded-lg transition-colors text-gray-400 hover:text-gray-600 disabled:text-blue-400"
        >
          <RefreshCw size={16} className={fetchingData ? 'animate-spin' : ''} />
        </button>

        {/* Divider */}
        <div className="w-px h-4 bg-gray-200 flex-shrink-0" />

        {/* Textarea */}
        <textarea
          ref={textRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
          }}
          onKeyDown={handleKey}
          placeholder="Soru sorun..."
          rows={1}
          className="flex-1 resize-none bg-transparent outline-none text-sm text-gray-800
                     placeholder-gray-400 leading-relaxed min-h-[22px] max-h-[120px] overflow-y-auto py-0.5"
        />

        {/* Send */}
        <button
          onClick={handleSend}
          disabled={!canSend}
          className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all
                     bg-black hover:bg-gray-800 disabled:bg-gray-100 text-white disabled:text-gray-300"
        >
          {loading ? (
            <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
          ) : (
            <svg className="w-3.5 h-3.5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z"/>
            </svg>
          )}
        </button>
      </div>

      {/* Dosya durumu */}
      {file && (
        <div className="mt-2 px-1">
          {/* Progress bar */}
          {uploadStatus === 'uploading' && (
            <div className="w-full h-0.5 bg-gray-100 rounded-full overflow-hidden mb-1.5">
              <div className="h-full bg-blue-500 rounded-full animate-[loading_1.5s_ease-in-out_infinite]"
                   style={{ width: '40%', animation: 'loading 1.5s ease-in-out infinite' }} />
            </div>
          )}

          <div className="flex items-center gap-2 text-xs">
            {/* Spinner veya ikon */}
            {uploadStatus === 'uploading' ? (
              <svg className="animate-spin h-3.5 w-3.5 text-blue-500 flex-shrink-0" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
            ) : uploadStatus === 'done' ? (
              <span className="text-green-500 flex-shrink-0">✓</span>
            ) : (
              <span className="text-red-400 flex-shrink-0">✗</span>
            )}

            <span className={`truncate max-w-[220px] ${
              uploadStatus === 'uploading' ? 'text-blue-500' :
              uploadStatus === 'done' ? 'text-green-600' : 'text-red-400'
            }`}>
              {uploadStatus === 'uploading' ? `${file.name} yükleniyor ve indeksleniyor...` :
               uploadStatus === 'done' ? `${file.name} hazır` :
               `${file.name} — hata`}
            </span>

            {uploadStatus !== 'uploading' && (
              <button
                onClick={() => { setFile(null); setUploadStatus('idle') }}
                className="ml-auto mr-4 flex-shrink-0 w-5 h-5 rounded-full bg-red-100 hover:bg-red-200
                           text-red-500 hover:text-red-600 flex items-center justify-center
                           text-sm font-bold transition-colors"
              >✕</button>
            )}
          </div>
        </div>
      )}

      {/* Fetch status */}
      {fetchMsg && (
        <p className={`mt-1.5 px-1 text-xs ${fetchMsg === 'Hata' ? 'text-red-400' : 'text-green-600'}`}>
          {fetchMsg === 'Hata' ? '✗ Veri güncellenemedi' : `✓ ${ticker} finansal verileri güncellendi`}
        </p>
      )}

      <style>{`
        @keyframes loading {
          0%   { transform: translateX(-100%); width: 40%; }
          50%  { width: 60%; }
          100% { transform: translateX(350%); width: 40%; }
        }
      `}</style>
    </div>
  )
}
