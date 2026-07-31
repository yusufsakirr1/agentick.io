import { useState, useEffect, useCallback } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import ChatPage from './pages/ChatPage'
import ComparePage from './pages/ComparePage'
import PortfolioPage from './pages/PortfolioPage'
import LoginPage from './pages/LoginPage'
import { MessageData } from './components/Message'
import { askQuestion } from './api/client'
import { useAuth } from './contexts/AuthContext'
import * as store from './services/conversationStorage'
import type { Conversation } from './services/conversationStorage'

export default function App() {
  const { user, loading: authLoading } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [defaultTicker, setDefaultTicker] = useState('THYAO')
  const [loading, setLoading] = useState(false)
  const [suggestion, setSuggestion] = useState<string | undefined>()

  // Kayıtlı konuşmaları localStorage'dan yükle
  useEffect(() => {
    if (user) setConversations(store.getAll())
  }, [user])

  const active = conversations.find(c => c.id === activeId) ?? null
  const messages = active?.messages ?? []
  const ticker = active?.ticker ?? defaultTicker

  const persist = useCallback((conversation: Conversation) => {
    store.upsert(conversation)
    setConversations(store.getAll())
  }, [])

  const handleTickerChange = useCallback((t: string) => {
    setDefaultTicker(t)
    if (active) persist({ ...active, ticker: t })
  }, [active, persist])

  const handleNewChat = useCallback(() => {
    setActiveId(null)
    setSuggestion(undefined)
  }, [])

  const handleSelectConversation = useCallback((id: string) => {
    setActiveId(id)
    setSuggestion(undefined)
  }, [])

  const handleDeleteConversation = useCallback((id: string) => {
    store.remove(id)
    setConversations(store.getAll())
    setActiveId(prev => (prev === id ? null : prev))
  }, [])

  const handleSend = async (question: string, t: string) => {
    setSuggestion(undefined)
    setDefaultTicker(t)

    // Aktif konuşma yoksa yeni bir tane başlat
    const base = active ?? store.createNew(t)
    const userMsg: MessageData = { id: crypto.randomUUID(), role: 'user', content: question }

    const withUserMessage: Conversation = {
      ...base,
      ticker: t,
      title: base.title || store.makeTitle(question),
      messages: [...base.messages, userMsg],
    }

    persist(withUserMessage)
    setActiveId(withUserMessage.id)
    setLoading(true)

    let reply: MessageData
    try {
      const history = withUserMessage.messages.map(m => ({ role: m.role, content: m.content }))
      const res = await askQuestion(question, t, history)
      reply = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: res.answer,
        ticker: t,
        meta: {
          sub_tasks: res.sub_tasks,
          retrieved_count: res.retrieved_count,
          retry_count: res.retry_count,
          sources: res.sources,
        },
      }
    } catch (e: unknown) {
      reply = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Bir hata oluştu: ${e instanceof Error ? e.message : 'Bilinmeyen hata'}`,
      }
    }

    // Yanıt, sorunun sorulduğu konuşmaya yazılır — kullanıcı arada
    // başka bir sohbete geçse bile doğru yere düşer.
    persist({ ...withUserMessage, messages: [...withUserMessage.messages, reply] })
    setLoading(false)
  }

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="w-8 h-8 border-4 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return <LoginPage />
  }

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden p-3 gap-3">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
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
          <Route path="/portfolio" element={<PortfolioPage />} />
        </Routes>
      </div>
    </div>
  )
}
