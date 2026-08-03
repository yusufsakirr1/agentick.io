import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { getProfile, isProfileSet, type UserProfile } from '../services/profileService'
import { describeFirestoreError, withFirestoreTimeout } from '../services/firebaseError'

interface ProfileContextType {
  profile: UserProfile
  /** En az bir tercih seçilmiş mi */
  profileSet: boolean
  /** İlk yükleme sürüyor mu — profil modalı buna bakar, kendisi istek atmaz */
  loading: boolean
  error: string | null
  setProfile: (p: UserProfile) => void
  reload: () => void
}

const ProfileContext = createContext<ProfileContextType | null>(null)

/**
 * Kullanıcı tercihlerini bir kez yükleyip sohbet / karşılaştırma / portföy
 * sayfalarının tamamına dağıtır — üçü de aynı profili agent'a gönderir.
 *
 * Okuma zaman aşımlıdır: Firestore erişilemezse promise hiç çözülmediği için
 * profil modalı sonsuza dek "yükleniyor" görünüyordu.
 */
export function ProfileProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [profile, setProfile] = useState<UserProfile>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  const uid = user?.uid ?? null

  const reload = useCallback(() => setAttempt(n => n + 1), [])

  useEffect(() => {
    if (!uid) {
      setProfile({})
      setError(null)
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    withFirestoreTimeout(getProfile(uid))
      .then(p => { if (!cancelled) setProfile(p) })
      .catch(e => {
        if (cancelled) return
        // Profil opsiyonel: hata sohbeti engellemez, sadece modalda gösterilir
        setError(`Tercihleriniz yüklenemedi. ${describeFirestoreError(e)}`)
      })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
  }, [uid, attempt])

  return (
    <ProfileContext.Provider
      value={{ profile, profileSet: isProfileSet(profile), loading, error, setProfile, reload }}
    >
      {children}
    </ProfileContext.Provider>
  )
}

export function useProfile() {
  const ctx = useContext(ProfileContext)
  if (!ctx) throw new Error('useProfile must be used within ProfileProvider')
  return ctx
}
