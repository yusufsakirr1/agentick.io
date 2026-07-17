import { useState } from 'react'
import AgentLogo from './AgentLogo'
import { Conversation, remove } from '../services/conversationStorage'
import { MessageCirclePlus, Clock } from 'lucide-react'

interface Props {
  conversations: Conversation[]
  activeId: string | null
  onSelect: (c: Conversation) => void
  onNew: () => void
  onDelete: (id: string) => void
}

export default function Sidebar({ conversations, activeId, onSelect, onNew, onDelete }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    remove(id)
    onDelete(id)
  }

  return (
    <aside className="w-72 flex-shrink-0 bg-white rounded-2xl shadow-sm flex flex-col overflow-hidden">

      {/* Üst — logo + yeni sohbet */}
      <div className="px-4 pt-5 pb-3">
        {/* Logo satırı */}
        <div className="flex items-center px-1 mb-5">
          <AgentLogo size={54} />
          <span
            style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
            className="text-[1.7rem] text-gray-900 leading-none tracking-tight -ml-1.5"
          >
            agentick.io
          </span>
        </div>

        {/* Yeni sohbet */}
        <button
          onClick={onNew}
          className="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl text-sm font-semibold
                     text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
        >
          <MessageCirclePlus className="w-5 h-5 text-gray-600 flex-shrink-0" strokeWidth={2} />
          Yeni Sohbet
        </button>
      </div>

      {/* Konuşma listesi */}
      <div className="flex-1 overflow-y-auto px-3 pb-4">
        {conversations.length > 0 && (
          <>
            <div className="flex items-center gap-2 px-2 mt-3 mb-2">
              <Clock className="w-3.5 h-3.5 text-gray-400" />
              <p className="text-xs font-semibold text-gray-500">Yakın zamandakiler</p>
            </div>

            <div className="space-y-0.5">
              {conversations.map(c => (
                <div
                  key={c.id}
                  onClick={() => onSelect(c)}
                  onMouseEnter={() => setHoveredId(c.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  className={`relative flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer
                              transition-colors select-none
                    ${activeId === c.id ? 'bg-gray-200/80' : 'hover:bg-gray-200/60'}`}
                >
                  {/* Başlık */}
                  <span className={`text-sm truncate flex-1 min-w-0
                    ${activeId === c.id ? 'text-gray-900 font-medium' : 'text-gray-700'}`}>
                    {c.title || 'Yeni sohbet'}
                  </span>

                  {/* Ticker badge — hover'da sil butonuyla yer değiştirir */}
                  {hoveredId === c.id ? (
                    <button
                      onClick={(e) => handleDelete(e, c.id)}
                      className="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors text-xs p-0.5"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    </button>
                  ) : (
                    <span className="flex-shrink-0 text-[10px] font-mono font-semibold text-gray-400">
                      {c.ticker}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {conversations.length === 0 && (
          <p className="text-xs text-gray-400 text-center px-4 pt-12">
            Henüz sohbet yok
          </p>
        )}
      </div>

      {/* Alt — kullanıcı */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-3 rounded-2xl hover:bg-gray-100 cursor-pointer transition-colors">
          <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            A
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900 truncate">Kullanıcı</p>
            <p className="text-xs text-gray-400 mt-0.5">agentick.io</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
