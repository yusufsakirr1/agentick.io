import { useState, useRef, useEffect } from 'react'
import AgentLogo from './components/AgentLogo'
import ChatInput from './components/ChatInput'
import Message, { MessageData } from './components/Message'
import Sidebar from './components/Sidebar'
import ThinkingIndicator from './components/ThinkingIndicator'
import { askQuestion } from './api/client'
import {
  Conversation,
  createNew,
  getAll,
  upsert,
  makeTitle,
} from './services/conversationStorage'

const SUGGESTIONS = [
  { label: 'Net marj analizi', q: 'Son 3 yılda net kâr marjı nasıl değişti?' },
  { label: 'Büyüme stratejisi', q: 'Yönetimin açıkladığı büyüme stratejisi nedir?' },
  { label: 'Bilanço özeti', q: 'Toplam varlıklar, borç ve özkaynak durumu nedir?' },
  { label: 'Nakit akışı', q: 'Operasyonel nakit akışı ve serbest nakit akışı nasıl?' },
]

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(getAll)
  const [active, setActive] = useState<Conversation | null>(null)
  const [defaultTicker, setDefaultTicker] = useState('THYAO')
  const [loading, setLoading] = useState(false)
  const [suggestion, setSuggestion] = useState<string | undefined>()
  const bottomRef = useRef<HTMLDivElement>(null)

  const messages: MessageData[] = active?.messages ?? []
  const ticker = active?.ticker ?? defaultTicker
  const hasMessages = messages.length > 0

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const syncConversations = () => setConversations(getAll())

  const handleNew = () => {
    setActive(null)
    setSuggestion(undefined)
  }

  const handleSelect = (c: Conversation) => {
    setActive(c)
    setSuggestion(undefined)
  }

  const handleDelete = (id: string) => {
    if (active?.id === id) setActive(null)
    syncConversations()
  }

  const handleTickerChange = (t: string) => {
    if (!active) {
      setDefaultTicker(t)
      return
    }
    const updated = { ...active, ticker: t }
    setActive(updated)
    upsert(updated)
    syncConversations()
  }

  const handleSend = async (question: string, t: string) => {
    setSuggestion(undefined)

    // Aktif konuşma yoksa yeni oluştur
    let conv = active ?? createNew(t)
    if (!active) conv = { ...conv, ticker: t }

    const userMsg: MessageData = { id: crypto.randomUUID(), role: 'user', content: question }
    const updatedMessages = [...conv.messages, userMsg]
    const title = conv.title || makeTitle(question)

    const updatedConv: Conversation = {
      ...conv,
      title,
      ticker: t,
      messages: updatedMessages,
      updatedAt: new Date().toISOString(),
    }
    setActive(updatedConv)
    upsert(updatedConv)
    syncConversations()
    setLoading(true)

    try {
      const history = updatedMessages.map(m => ({ role: m.role, content: m.content }))
      const res = await askQuestion(question, t, history)

      const aiMsg: MessageData = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: res.answer,
        ticker: t,
        meta: {
          sub_tasks: res.sub_tasks,
          retrieved_count: res.retrieved_count,
          retry_count: res.retry_count,
        },
      }

      const finalConv: Conversation = {
        ...updatedConv,
        messages: [...updatedMessages, aiMsg],
        updatedAt: new Date().toISOString(),
      }
      setActive(finalConv)
      upsert(finalConv)
      syncConversations()
    } catch (e: unknown) {
      const errMsg: MessageData = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Bir hata oluştu: ${e instanceof Error ? e.message : 'Bilinmeyen hata'}`,
      }
      const finalConv: Conversation = {
        ...updatedConv,
        messages: [...updatedMessages, errMsg],
        updatedAt: new Date().toISOString(),
      }
      setActive(finalConv)
      upsert(finalConv)
      syncConversations()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden p-3 gap-3">

      {/* ── Sol sidebar ── */}
      <Sidebar
        conversations={conversations}
        activeId={active?.id ?? null}
        onSelect={handleSelect}
        onNew={handleNew}
        onDelete={handleDelete}
      />

      {/* ── Ana alan ── */}
      <div className="flex-1 flex flex-col min-w-0 bg-white rounded-2xl overflow-hidden shadow-sm">

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
              onChange={(e) => handleTickerChange(e.target.value)}
              className="text-xs font-mono font-semibold text-gray-500 bg-gray-100 px-2 py-1 rounded-lg
                         border-none outline-none cursor-pointer appearance-none hover:bg-gray-200 transition-colors"
            >
              {['AKBNK','AKSEN','ARCLK','ASELS','BIMAS','EKGYO','ENKAI','EREGL','FROTO','GARAN',
                'GUBRF','HALKB','ISCTR','KCHOL','KONTR','KOZAL','KRDMD','ODAS','PETKM','PGSUS',
                'SAHOL','SASA','SISE','TAVHL','TCELL','THYAO','TOASO','TUPRS','VAKBN','YKBNK'].map(t => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </header>
        )}

        {/* İçerik */}
        {!hasMessages ? (

          /* Boş durum */
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
              onSend={handleSend}
              loading={loading}
              ticker={ticker}
              onTickerChange={handleTickerChange}
              initialQuestion={suggestion}
            />

            <div className="flex flex-wrap gap-2 justify-center max-w-xl">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.label}
                  onClick={() => setSuggestion(s.q)}
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

          /* Sohbet */
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
                onSend={handleSend}
                loading={loading}
                ticker={ticker}
                onTickerChange={handleTickerChange}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
