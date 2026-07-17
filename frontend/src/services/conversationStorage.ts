import { MessageData } from '../components/Message'

export interface Conversation {
  id: string
  title: string
  ticker: string
  messages: MessageData[]
  createdAt: string
  updatedAt: string
}

const KEY = 'agentick_conversations'

function load(): Conversation[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]')
  } catch {
    return []
  }
}

function save(conversations: Conversation[]) {
  localStorage.setItem(KEY, JSON.stringify(conversations))
}

export function getAll(): Conversation[] {
  return load().sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
}

export function getById(id: string): Conversation | null {
  return load().find(c => c.id === id) ?? null
}

export function upsert(conversation: Conversation) {
  const all = load()
  const idx = all.findIndex(c => c.id === conversation.id)
  if (idx >= 0) {
    all[idx] = { ...conversation, updatedAt: new Date().toISOString() }
  } else {
    all.unshift(conversation)
  }
  save(all)
}

export function remove(id: string) {
  save(load().filter(c => c.id !== id))
}

export function createNew(ticker: string): Conversation {
  return {
    id: crypto.randomUUID(),
    title: '',
    ticker,
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
}

export function makeTitle(firstUserMessage: string): string {
  return firstUserMessage.length > 38
    ? firstUserMessage.slice(0, 38) + '…'
    : firstUserMessage
}

/** Tarih gruplama */
export function groupByDate(conversations: Conversation[]): Record<string, Conversation[]> {
  const now = new Date()
  const today = now.toDateString()
  const yesterday = new Date(now.getTime() - 86400000).toDateString()
  const weekAgo = new Date(now.getTime() - 7 * 86400000)

  const groups: Record<string, Conversation[]> = {
    'Bugün': [],
    'Dün': [],
    'Bu Hafta': [],
    'Daha Önce': [],
  }

  for (const c of conversations) {
    const d = new Date(c.updatedAt)
    const ds = d.toDateString()
    if (ds === today) groups['Bugün'].push(c)
    else if (ds === yesterday) groups['Dün'].push(c)
    else if (d >= weekAgo) groups['Bu Hafta'].push(c)
    else groups['Daha Önce'].push(c)
  }

  return groups
}
