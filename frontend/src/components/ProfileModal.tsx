import { useState, useEffect } from 'react'
import { X, AlertTriangle, Check, RefreshCw } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useProfile } from '../contexts/ProfileContext'
import { describeFirestoreError, withFirestoreTimeout } from '../services/firebaseError'
import {
  saveProfile,
  RISK_LABELS, RISK_HINTS, HORIZON_LABELS, FOCUS_LABELS,
  EXPERIENCE_LABELS, EXPERIENCE_HINTS,
  type UserProfile, type RiskProfile, type Horizon, type FocusArea, type Experience,
} from '../services/profileService'

interface Props {
  onClose: () => void
  onSaved: (profile: UserProfile) => void
}

/** Tek seçimli seçenek satırı */
function OptionRow<T extends string>({
  options, hints, value, onChange,
}: {
  options: Record<T, string>
  hints?: Record<T, string>
  value: T | undefined
  onChange: (v: T | undefined) => void
}) {
  return (
    <div className="space-y-1.5">
      {(Object.keys(options) as T[]).map(key => {
        const selected = value === key
        return (
          <button
            key={key}
            // Seçiliye tekrar basmak tercihi temizler — "belirtmek istemiyorum" hâli
            onClick={() => onChange(selected ? undefined : key)}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl border text-left
                        transition-colors cursor-pointer
              ${selected
                ? 'border-gray-900 bg-gray-900 text-white'
                : 'border-gray-200 hover:border-gray-400 text-gray-700'
              }`}
          >
            <span className="flex-1 min-w-0">
              <span className="block text-sm font-medium">{options[key]}</span>
              {hints?.[key] && (
                <span className={`block text-[11px] mt-0.5 ${selected ? 'text-gray-300' : 'text-gray-400'}`}>
                  {hints[key]}
                </span>
              )}
            </span>
            {selected && <Check className="w-4 h-4 flex-shrink-0" strokeWidth={2.5} />}
          </button>
        )
      })}
    </div>
  )
}

export default function ProfileModal({ onClose, onSaved }: Props) {
  const { user } = useAuth()
  // Profil uygulama açılışında bir kez yükleniyor; modal kendi isteğini atmaz.
  // Eskiden burada ikinci bir getProfile vardı ve Firestore erişilemezse
  // modal sonsuza dek "yükleniyor" görünüyordu.
  const { profile: loadedProfile, loading, error: loadError, reload } = useProfile()

  const [profile, setProfile] = useState<UserProfile>(loadedProfile)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Arka planda yükleme tamamlanırsa formu tazele (kullanıcı henüz dokunmadıysa)
  useEffect(() => {
    if (!loading) setProfile(loadedProfile)
  }, [loading, loadedProfile])

  const error = saveError ?? loadError

  const toggleFocus = (area: FocusArea) => {
    setProfile(p => {
      const current = p.focus ?? []
      return {
        ...p,
        focus: current.includes(area)
          ? current.filter(f => f !== area)
          : [...current, area],
      }
    })
  }

  const handleSave = async () => {
    if (!user) return
    setSaving(true)
    setSaveError(null)
    try {
      await withFirestoreTimeout(saveProfile(user.uid, profile))
      onSaved(profile)
      onClose()
    } catch (e) {
      setSaveError(`Tercihleriniz kaydedilemedi. ${describeFirestoreError(e)}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg max-h-[85vh] flex flex-col bg-white rounded-2xl shadow-xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Başlık */}
        <div className="flex-shrink-0 flex items-start gap-3 px-6 py-5 border-b border-gray-100">
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold text-gray-900">Yatırımcı Profili</h2>
            <p className="text-xs text-gray-400 mt-1 leading-relaxed">
              Tercihleriniz cevapların <strong className="font-medium text-gray-500">hangi verilere
              ağırlık vereceğini</strong> ve dilin ne kadar teknik olacağını belirler.
              Yatırım tavsiyesi üretmez.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100
                       transition-colors cursor-pointer flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* İçerik */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="w-6 h-6 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
            </div>
          ) : (
            <>
              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2.5">
                  Yaklaşım
                </h3>
                <OptionRow<RiskProfile>
                  options={RISK_LABELS}
                  hints={RISK_HINTS}
                  value={profile.riskProfile}
                  onChange={v => setProfile(p => ({ ...p, riskProfile: v }))}
                />
              </section>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2.5">
                  Yatırım Vadesi
                </h3>
                <OptionRow<Horizon>
                  options={HORIZON_LABELS}
                  value={profile.horizon}
                  onChange={v => setProfile(p => ({ ...p, horizon: v }))}
                />
              </section>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2.5">
                  İlgi Alanları <span className="normal-case font-normal">(birden fazla seçilebilir)</span>
                </h3>
                <div className="flex flex-wrap gap-2">
                  {(Object.keys(FOCUS_LABELS) as FocusArea[]).map(area => {
                    const selected = profile.focus?.includes(area) ?? false
                    return (
                      <button
                        key={area}
                        onClick={() => toggleFocus(area)}
                        className={`px-3.5 py-1.5 rounded-full text-xs font-medium border
                                    transition-colors cursor-pointer
                          ${selected
                            ? 'border-gray-900 bg-gray-900 text-white'
                            : 'border-gray-200 text-gray-600 hover:border-gray-400'
                          }`}
                      >
                        {FOCUS_LABELS[area]}
                      </button>
                    )
                  })}
                </div>
              </section>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2.5">
                  Finans Bilgisi
                </h3>
                <OptionRow<Experience>
                  options={EXPERIENCE_LABELS}
                  hints={EXPERIENCE_HINTS}
                  value={profile.experience}
                  onChange={v => setProfile(p => ({ ...p, experience: v }))}
                />
              </section>
            </>
          )}

          {error && (
            <div className="flex items-start gap-2 text-xs bg-amber-50 border border-amber-200
                            text-amber-900 px-3 py-2.5 rounded-xl">
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" strokeWidth={2} />
              <p className="flex-1 leading-relaxed">{error}</p>
              {!saveError && (
                <button
                  onClick={reload}
                  className="flex-shrink-0 flex items-center gap-1 font-medium px-2 py-1 rounded-lg
                             bg-white border border-amber-200 hover:bg-amber-100
                             transition-colors cursor-pointer"
                >
                  <RefreshCw className="w-3 h-3" />
                  Yeniden dene
                </button>
              )}
            </div>
          )}
        </div>

        {/* Alt */}
        <div className="flex-shrink-0 flex items-center justify-end gap-2 px-6 py-4 border-t border-gray-100">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700
                       transition-colors cursor-pointer"
          >
            Vazgeç
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="px-5 py-2 text-sm font-medium text-white bg-gray-900 hover:bg-gray-800
                       disabled:bg-gray-300 rounded-xl transition-colors cursor-pointer"
          >
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </div>
      </div>
    </div>
  )
}
