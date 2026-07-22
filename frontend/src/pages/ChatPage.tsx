import { useRef, useEffect } from 'react'
import AgentLogo from '../components/AgentLogo'
import ChatInput from '../components/ChatInput'
import Message, { MessageData } from '../components/Message'
import ThinkingIndicator from '../components/ThinkingIndicator'
import { BIST_TICKERS } from '../constants/tickers'

const SUGGESTIONS = [
  { label: 'Net marj analizi', q: 'Son 3 yılda net kâr marjı nasıl değişti?' },
  { label: 'Büyüme stratejisi', q: 'Yönetimin açıkladığı büyüme stratejisi nedir?' },
  { label: 'Bilanço özeti', q: 'Toplam varlıklar, borç ve özkaynak durumu nedir?' },
  { label: 'Nakit akışı', q: 'Operasyonel nakit akışı ve serbest nakit akışı nasıl?' },
]

interface Props {
  messages: MessageData[]
  ticker: string
  loading: boolean
  suggestion: string | undefined
  onSend: (question: string, ticker: string) => void
  onTickerChange: (t: string) => void
  onSuggestion: (q: string) => void
}

export default function ChatPage({
  messages,
  ticker,
  loading,
  suggestion,
  onSend,
  onTickerChange,
  onSuggestion,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const hasMessages = messages.length > 0

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <>
      {/* Header (sadece chat modunda) */}
      {hasMessages && (
        <header className="flex-shrink-0 flex items-center justify-between px-6 py-3 border-b border-gray-100">
          <div className="flex items-center gap-0">
            <AgentLogo size={50} />
            <span
              style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
              className="text-[2.4rem] text-gray-900 leading-none tracking-tight -ml-2"
            >
              agentick.io
            </span>
          </div>
          <select
            value={ticker}
            onChange={(e) => onTickerChange(e.target.value)}
            className="text-xs font-mono font-semibold text-gray-500 bg-gray-100 px-2 py-1 rounded-lg
                       border-none outline-none cursor-pointer appearance-none hover:bg-gray-200 transition-colors"
          >
            {BIST_TICKERS.map(t => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </header>
      )}

      {/* Content */}
      {!hasMessages ? (
        /* Empty state */
        <div className="flex-1 flex flex-col items-center justify-center px-4 pb-24 gap-6">
          <div className="flex items-center gap-0">
            <AgentLogo size={80} />
            <span
              style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
              className="text-[3.5rem] text-gray-900 leading-none tracking-tight -ml-3"
            >
              agentick.io
            </span>
          </div>

          <h1
            style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
            className="text-[2.3rem] text-gray-900 text-center leading-tight"
          >
            Nasıl yardımcı olabilirim?
          </h1>

          <ChatInput
            onSend={onSend}
            loading={loading}
            ticker={ticker}
            onTickerChange={onTickerChange}
            initialQuestion={suggestion}
          />

          <div className="flex flex-wrap gap-2 justify-center max-w-xl">
            {SUGGESTIONS.map((s) => (
              <button
                key={s.label}
                onClick={() => onSuggestion(s.q)}
                className="px-4 py-2 rounded-full border border-gray-200 text-sm text-gray-600
                           hover:border-gray-400 hover:text-gray-900 hover:bg-gray-50
                           transition-all font-medium"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Chat */
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto px-8 py-8">
            <div className="max-w-4xl mx-auto space-y-8">
              {messages.map(m => <Message key={m.id} message={m} />)}

              {loading && (
                <div className="flex gap-3 items-start">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                                  shadow-[0_0_0_1.5px_rgba(0,0,0,0.12),0_2px_8px_rgba(0,0,0,0.10)]">
                    <AgentLogo size={44} color="#111111" />
                  </div>
                  <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm shadow-sm px-5 py-4">
                    <ThinkingIndicator />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </div>

          <div className="flex-shrink-0 border-t border-gray-100 bg-white px-4 py-4">
            <ChatInput
              onSend={onSend}
              loading={loading}
              ticker={ticker}
              onTickerChange={onTickerChange}
            />
          </div>
        </div>
      )}
    </>
  )
}
