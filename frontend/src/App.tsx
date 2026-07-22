import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import ChatPage from './pages/ChatPage'
import ComparePage from './pages/ComparePage'
import { MessageData } from './components/Message'
import { askQuestion } from './api/client'
import {
  Conversation,
  createNew,
  getAll,
  upsert,
  makeTitle,
} from './services/conversationStorage'

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(getAll)
  const [active, setActive] = useState<Conversation | null>(null)
  const [defaultTicker, setDefaultTicker] = useState('THYAO')
  const [loading, setLoading] = useState(false)
  const [suggestion, setSuggestion] = useState<string | undefined>()

  const messages: MessageData[] = active?.messages ?? []
  const ticker = active?.ticker ?? defaultTicker

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
      <Sidebar
        conversations={conversations}
        activeId={active?.id ?? null}
        onSelect={handleSelect}
        onNew={handleNew}
        onDelete={handleDelete}
      />

      <div className="flex-1 flex flex-col min-w-0 bg-white rounded-2xl overflow-hidden shadow-sm">
        <Routes>
          <Route
            path="/"
            element={
              <ChatPage
                messages={messages}
                ticker={ticker}
                loading={loading}
                suggestion={suggestion}
                onSend={handleSend}
                onTickerChange={handleTickerChange}
                onSuggestion={setSuggestion}
              />
            }
          />
          <Route path="/compare" element={<ComparePage />} />
        </Routes>
      </div>
    </div>
  )
}
