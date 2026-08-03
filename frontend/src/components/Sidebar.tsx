import { useNavigate, useLocation } from 'react-router-dom'
import AgentLogo from './AgentLogo'
import {
  MessageCircle, GitCompareArrows, Briefcase, LogOut, MessageCirclePlus, X,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { groupByDate, type Conversation } from '../services/conversationStorage'

const NAV_ITEMS = [
  { label: 'Sohbet', path: '/', icon: MessageCircle },
  { label: 'Karşılaştır', path: '/compare', icon: GitCompareArrows },
  { label: 'Portföy', path: '/portfolio', icon: Briefcase },
]

interface Props {
  conversations: Conversation[]
  activeId: string | null
  profileSet: boolean
  onNewChat: () => void
  onSelectConversation: (id: string) => void
  onDeleteConversation: (id: string) => void
  onOpenProfile: () => void
}

export default function Sidebar({
  conversations,
  activeId,
  profileSet,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  onOpenProfile,
}: Props) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { user, signOut } = useAuth()

  const groups = groupByDate(conversations)

  const handleNewChat = () => {
    onNewChat()
    navigate('/')
  }

  const handleSelect = (id: string) => {
    onSelectConversation(id)
    navigate('/')
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-white rounded-2xl shadow-sm flex flex-col overflow-hidden">
      {/* Logo */}
      <div className="px-4 pt-5 pb-4">
        <div className="flex items-center px-1">
          <AgentLogo size={54} />
          <span
            style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
            className="text-[1.7rem] text-gray-900 leading-none tracking-tight -ml-1.5"
          >
            agentick.io
          </span>
        </div>
      </div>

      {/* Yeni sohbet */}
      <div className="px-3 pb-3">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                     text-white bg-gray-900 hover:bg-gray-800 transition-colors cursor-pointer"
        >
          <MessageCirclePlus className="w-4 h-4 flex-shrink-0" />
          Yeni Sohbet
        </button>
      </div>

      {/* Navigasyon */}
      <nav className="px-3 space-y-1">
        {NAV_ITEMS.map(item => {
          const active = pathname === item.path
          const Icon = item.icon
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium
                          transition-colors cursor-pointer
                ${active
                  ? 'bg-gray-100 text-gray-900 font-semibold'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" strokeWidth={active ? 2.2 : 1.8} />
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* Konuşma geçmişi */}
      <div className="flex-1 min-h-0 overflow-y-auto px-3 mt-3">
        {conversations.length === 0 ? (
          <p className="px-3 py-4 text-xs text-gray-300">Henüz sohbet yok.</p>
        ) : (
          Object.entries(groups).map(([label, items]) =>
            items.length === 0 ? null : (
              <div key={label} className="mb-3">
                <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-300">
                  {label}
                </p>
                {items.map(c => {
                  const isActive = c.id === activeId
                  return (
                    <div
                      key={c.id}
                      className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
                                  transition-colors ${isActive ? 'bg-gray-100' : 'hover:bg-gray-50'}`}
                      onClick={() => handleSelect(c.id)}
                    >
                      <span className="text-[10px] font-mono font-bold text-gray-400 flex-shrink-0">
                        {c.ticker}
                      </span>
                      <span
                        className={`flex-1 min-w-0 truncate text-xs ${
                          isActive ? 'text-gray-900 font-medium' : 'text-gray-600'
                        }`}
                        title={c.title || 'Yeni sohbet'}
                      >
                        {c.title || 'Yeni sohbet'}
                      </span>
                      <button
                        onClick={(e) => { e.stopPropagation(); onDeleteConversation(c.id) }}
                        title="Sohbeti sil"
                        className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-gray-300
                                   hover:text-red-500 transition-all flex-shrink-0"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )
                })}
              </div>
            )
          )
        )}
      </div>

      {/* Alt kısım */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-3 rounded-2xl">
          {/* Profil alanına tıklayınca tercihler açılır */}
          <button
            onClick={onOpenProfile}
            title="Yatırımcı profilini düzenle"
            className="flex items-center gap-3 min-w-0 flex-1 text-left rounded-xl
                       hover:bg-gray-50 -mx-1 px-1 py-1 transition-colors cursor-pointer"
          >
            <div className="relative flex-shrink-0">
              {user?.photoURL ? (
                <img
                  src={user.photoURL}
                  alt=""
                  className="w-10 h-10 rounded-full"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center text-white text-sm font-bold">
                  {user?.displayName?.[0] ?? 'U'}
                </div>
              )}
              {/* Profil doluysa yeşil nokta, boşsa "ayarla" çağrısı */}
              {profileSet && (
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full
                                 bg-emerald-500 border-2 border-white" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {user?.displayName ?? 'Kullanıcı'}
              </p>
              <p className={`text-xs mt-0.5 truncate ${profileSet ? 'text-gray-400' : 'text-gray-900 font-medium'}`}>
                {profileSet ? (user?.email ?? '') : 'Profilini ayarla'}
              </p>
            </div>
          </button>
          <button
            onClick={signOut}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors cursor-pointer flex-shrink-0"
            title="Çıkış Yap"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
