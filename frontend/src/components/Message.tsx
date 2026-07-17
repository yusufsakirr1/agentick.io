import ReactMarkdown from 'react-markdown'
import AgentLogo from './AgentLogo'

export interface MessageData {
  id: string
  role: 'user' | 'assistant'
  content: string
  ticker?: string
  meta?: {
    sub_tasks?: Array<{ query: string; type: string }>
    retrieved_count?: number
    retry_count?: number
  }
}

export default function Message({ message }: { message: MessageData }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse ml-auto' : 'flex-row mr-auto w-full'}`}>
      {/* Avatar */}
      {isUser ? (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-black flex items-center justify-center text-sm font-bold text-white">
          S
        </div>
      ) : (
        <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                        shadow-[0_0_0_1.5px_rgba(0,0,0,0.12),0_2px_8px_rgba(0,0,0,0.10)]">
          <AgentLogo size={44} color="#111111" />
        </div>
      )}

      {/* Content */}
      <div className={`flex flex-col gap-1.5 ${isUser ? 'items-end max-w-[70%]' : 'items-start max-w-[85%]'}`}>
        <div className={`
          rounded-2xl px-5 py-4 text-[15px] leading-7
          ${isUser
            ? 'bg-black text-white rounded-tr-sm'
            : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm shadow-sm'
          }
        `}>
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="prose prose-base prose-gray max-w-none
                            prose-p:my-1.5 prose-p:leading-7
                            prose-ul:my-1.5 prose-li:my-1
                            prose-strong:font-semibold prose-strong:text-gray-900
                            prose-headings:hidden">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Meta chips */}
        {!isUser && message.meta && (
          <div className="flex gap-1.5 flex-wrap">
            {/* Kullanılan araçlar — tekrarsız */}
            {Array.from(new Set(message.meta.sub_tasks?.map(t => t.type) ?? [])).map(type => (
              <span key={type} className={`text-[11px] px-2 py-0.5 rounded-full font-medium
                ${type === 'sql' ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'}`}>
                {type === 'sql' ? '⚡ SQL' : '🔍 Vektör'}
              </span>
            ))}
            {(message.meta.retry_count ?? 0) > 1 && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-600">
                {message.meta.retry_count! - 1}× retry
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
