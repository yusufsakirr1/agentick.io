import { useState, useRef, useEffect } from 'react'
import AgentLogo from './AgentLogo'
import Message, { MessageData } from './Message'
import ThinkingIndicator from './ThinkingIndicator'
import { askCompareQuestion } from '../api/client'

interface Props {
  tickers: string[]
}

export default function ComparisonChat({ tickers }: Props) {
  const [messages, setMessages] = useState<MessageData[]>([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textRef = useRef<HTMLTextAreaElement>(null)
  const prevTickersRef = useRef<string>(tickers.join(','))

  // Ticker değişince chat sıfırla
  useEffect(() => {
    const key = tickers.join(',')
    if (key !== prevTickersRef.current) {
      setMessages([])
      prevTickersRef.current = key
    }
  }, [tickers])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = async () => {
    const q = text.trim()
    if (!q || loading) return

    const userMsg: MessageData = { id: crypto.randomUUID(), role: 'user', content: q }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setText('')
    setLoading(true)

    try {
      const history = updatedMessages.map(m => ({ role: m.role, content: m.content }))
      const res = await askCompareQuestion(q, tickers, history)

      if (res.error) {
        const errMsg: MessageData = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Hata: ${res.error}`,
        }
        setMessages(prev => [...prev, errMsg])
        return
      }

      const aiMsg: MessageData = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: res.answer,
        meta: {
          sub_tasks: res.sub_tasks,
          retrieved_count: res.retrieved_count,
          retry_count: res.retry_count,
        },
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (e: unknown) {
      const errMsg: MessageData = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Hata: ${e instanceof Error ? e.message : 'Bilinmeyen hata'}`,
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const canSend = text.trim().length > 0 && !loading

  return (
    <div className="flex flex-col">
      {/* Mesajlar */}
      {messages.length > 0 && (
        <div className="max-h-[500px] overflow-y-auto px-2 py-4">
          <div className="space-y-6">
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
      )}

      {/* Input */}
      <div className="flex items-center gap-2 bg-white rounded-full px-4 py-3
                      shadow-[0_2px_20px_rgba(0,0,0,0.09)] ring-1 ring-gray-100">
        {/* Seçili ticker badge'leri (read-only) */}
        <div className="flex gap-1 flex-shrink-0">
          {tickers.map(t => (
            <span key={t} className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
              {t}
            </span>
          ))}
        </div>

        <div className="w-px h-4 bg-gray-200 flex-shrink-0" />

        <textarea
          ref={textRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
          }}
          onKeyDown={handleKey}
          placeholder="Karşılaştırma sorusu sorun..."
          rows={1}
          className="flex-1 resize-none bg-transparent outline-none text-sm text-gray-800
                     placeholder-gray-400 leading-relaxed min-h-[22px] max-h-[120px] overflow-y-auto py-0.5"
        />

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
    </div>
  )
}
