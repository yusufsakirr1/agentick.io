import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import ChatPage from './pages/ChatPage'
import ComparePage from './pages/ComparePage'
import LoginPage from './pages/LoginPage'
import { MessageData } from './components/Message'
import { askQuestion } from './api/client'
import { useAuth } from './contexts/AuthContext'

export default function App() {
  const { user, loading: authLoading } = useAuth()
  const [messages, setMessages] = useState<MessageData[]>([])
  const [ticker, setTicker] = useState('THYAO')
  const [loading, setLoading] = useState(false)
  const [suggestion, setSuggestion] = useState<string | undefined>()

  const handleSend = async (question: string, t: string) => {
    setSuggestion(undefined)
    const userMsg: MessageData = { id: crypto.randomUUID(), role: 'user', content: question }
    const updated = [...messages, userMsg]
    setMessages(updated)
    setTicker(t)
    setLoading(true)

    try {
      const history = updated.map(m => ({ role: m.role, content: m.content }))
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
      setMessages(prev => [...prev, aiMsg])
    } catch (e: unknown) {
      const errMsg: MessageData = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Bir hata oluştu: ${e instanceof Error ? e.message : 'Bilinmeyen hata'}`,
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
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
      <Sidebar />

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
                onTickerChange={setTicker}
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
