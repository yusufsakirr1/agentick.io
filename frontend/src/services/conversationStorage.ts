import { MessageData } from '../components/Message'

export interface Conversation {
  id: string
  title: string
  ticker: string
  messages: MessageData[]
  createdAt: string
  updatedAt: string
}

/**
 * Sohbetler kullanıcı bazında saklanır: `agentick_conversations_{uid}`.
 *
 * Eskiden tek bir `agentick_conversations` anahtarı vardı; aynı bilgisayarda
 * ikinci bir hesapla giriş yapan kullanıcı öncekinin tüm sohbetlerini görüyordu.
 */
const LEGACY_KEY = 'agentick_conversations'

function keyFor(uid: string): string {
  return `${LEGACY_KEY}_${uid}`
}

function load(uid: string): Conversation[] {
  try {
    return JSON.parse(localStorage.getItem(keyFor(uid)) ?? '[]')
  } catch {
    return []
  }
}

function save(uid: string, conversations: Conversation[]) {
  localStorage.setItem(keyFor(uid), JSON.stringify(conversations))
}

/**
 * Anahtarsız eski kayıtları ilk giriş yapan kullanıcıya bir kereliğine taşır.
 * Taşıma sonrası eski anahtar silinir, böylece ikinci kullanıcıya sızmaz.
 */
export function migrateLegacy(uid: string) {
  const legacy = localStorage.getItem(LEGACY_KEY)
  if (legacy === null) return

  if (localStorage.getItem(keyFor(uid)) === null) {
    localStorage.setItem(keyFor(uid), legacy)
  }
  localStorage.removeItem(LEGACY_KEY)
}

export function getAll(uid: string): Conversation[] {
  return load(uid).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
}

export function getById(uid: string, id: string): Conversation | null {
  return load(uid).find(c => c.id === id) ?? null
}

export function upsert(uid: string, conversation: Conversation) {
  const all = load(uid)
  const idx = all.findIndex(c => c.id === conversation.id)
  if (idx >= 0) {
    all[idx] = { ...conversation, updatedAt: new Date().toISOString() }
  } else {
    all.unshift(conversation)
  }
  save(uid, all)
}

export function remove(uid: string, id: string) {
  save(uid, load(uid).filter(c => c.id !== id))
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
