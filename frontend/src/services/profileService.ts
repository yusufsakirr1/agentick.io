import { doc, getDoc, setDoc } from 'firebase/firestore'
import { db } from '../config/firebase'

/**
 * Kullanıcı tercihleri — cevabın vurgusunu ve dilini belirler.
 * Yatırım tavsiyesi üretmez; backend'de `src/agent/user_profile.py` tarafından
 * beyaz listeye sokulup synthesizer system prompt'una eklenir.
 */
export interface UserProfile {
  riskProfile?: RiskProfile
  horizon?: Horizon
  focus?: FocusArea[]
  experience?: Experience
}

export type RiskProfile = 'temkinli' | 'dengeli' | 'agresif'
export type Horizon = 'kisa' | 'orta' | 'uzun'
export type FocusArea = 'temettu' | 'buyume' | 'deger' | 'likidite'
export type Experience = 'baslangic' | 'orta' | 'ileri'

/** Etiketler — backend'deki anahtarlarla birebir aynı olmalı */
export const RISK_LABELS: Record<RiskProfile, string> = {
  temkinli: 'Temkinli',
  dengeli: 'Dengeli',
  agresif: 'Büyüme odaklı',
}

export const RISK_HINTS: Record<RiskProfile, string> = {
  temkinli: 'Borçluluk, likidite ve nakit akışı öne çıkar',
  dengeli: 'Büyüme ve risk eşit ağırlıkta',
  agresif: 'Büyüme oranları ve marj genişlemesi öne çıkar',
}

export const HORIZON_LABELS: Record<Horizon, string> = {
  kisa: '1 yıldan az',
  orta: '1-3 yıl',
  uzun: '3 yıldan fazla',
}

export const FOCUS_LABELS: Record<FocusArea, string> = {
  temettu: 'Temettü',
  buyume: 'Büyüme',
  deger: 'Değerleme',
  likidite: 'Likidite',
}

export const EXPERIENCE_LABELS: Record<Experience, string> = {
  baslangic: 'Yeni başlıyorum',
  orta: 'Orta düzey',
  ileri: 'Deneyimliyim',
}

export const EXPERIENCE_HINTS: Record<Experience, string> = {
  baslangic: 'Teknik terimler parantez içinde açıklanır',
  orta: 'Varsayılan anlatım',
  ileri: 'Terimler açıklanmadan kullanılır',
}

function profileRef(uid: string) {
  return doc(db, 'users', uid, 'profile', 'default')
}

export async function getProfile(uid: string): Promise<UserProfile> {
  const snap = await getDoc(profileRef(uid))
  if (!snap.exists()) return {}
  return (snap.data() ?? {}) as UserProfile
}

export async function saveProfile(uid: string, profile: UserProfile): Promise<void> {
  await setDoc(profileRef(uid), profile)
}

/** Profilde en az bir tercih seçilmiş mi? */
export function isProfileSet(profile: UserProfile): boolean {
  return Boolean(
    profile.riskProfile || profile.horizon || profile.experience || profile.focus?.length,
  )
}
