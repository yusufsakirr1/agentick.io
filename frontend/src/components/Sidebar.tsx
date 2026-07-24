import { useNavigate, useLocation } from 'react-router-dom'
import AgentLogo from './AgentLogo'
import { MessageCircle, GitCompareArrows, Briefcase, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const NAV_ITEMS = [
  { label: 'Sohbet', path: '/', icon: MessageCircle },
  { label: 'Karşılaştır', path: '/compare', icon: GitCompareArrows },
  { label: 'Portföy', path: '/portfolio', icon: Briefcase },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { user, signOut } = useAuth()

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

      {/* Navigasyon */}
      <nav className="flex-1 px-3 space-y-1">
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

      {/* Alt kısım */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-3 rounded-2xl">
          {user?.photoURL ? (
            <img
              src={user.photoURL}
              alt=""
              className="w-10 h-10 rounded-full flex-shrink-0"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
              {user?.displayName?.[0] ?? 'U'}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900 truncate">
              {user?.displayName ?? 'Kullanıcı'}
            </p>
            <p className="text-xs text-gray-400 mt-0.5 truncate">
              {user?.email ?? ''}
            </p>
          </div>
          <button
            onClick={signOut}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors cursor-pointer"
            title="Çıkış Yap"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
