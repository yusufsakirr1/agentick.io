/**
 * Firestore hatalarını kullanıcıya gösterilebilir Türkçe mesaja çevirir.
 *
 * Bu dosyanın varlık sebebi: hatalar daha önce sessizce yutuluyordu ve kullanıcı
 * kaydedilmemiş portföyünü boş bir liste olarak görüyordu — "silinmiş" gibi.
 */

const MESSAGES: Record<string, string> = {
  'permission-denied':
    'Firestore erişim izni reddedildi. Projedeki firestore.rules dosyasındaki kuralların Firebase konsoluna yüklendiğinden emin olun.',
  unauthenticated: 'Oturumunuz düşmüş görünüyor. Lütfen tekrar giriş yapın.',
  unavailable: 'Firestore\'a şu anda ulaşılamıyor. İnternet bağlantınızı kontrol edin.',
  'failed-precondition':
    'Firestore veritabanı bu projede etkin değil. Firebase konsolundan Firestore\'u oluşturun.',
  'not-found': 'Firestore veritabanı bulunamadı. Firebase konsolundan Firestore\'u oluşturun.',
  'deadline-exceeded': 'Firestore isteği zaman aşımına uğradı. Tekrar deneyin.',
  'resource-exhausted': 'Firestore kotası doldu. Bir süre sonra tekrar deneyin.',
}

export function describeFirestoreError(e: unknown): string {
  const code = (e as { code?: string } | null)?.code
  if (code) {
    // Kodlar "firestore/permission-denied" biçiminde de gelebiliyor
    const short = code.includes('/') ? code.split('/')[1] : code
    if (MESSAGES[short]) return MESSAGES[short]
    return `Firestore hatası (${code}).`
  }
  return e instanceof Error && e.message
    ? `Firestore hatası: ${e.message}`
    : 'Firestore ile iletişim kurulamadı.'
}

/** Firestore erişilemez olduğunda okumanın süresiz asılı kalmaması için üst sınır */
export const FIRESTORE_TIMEOUT_MS = 8000

class FirestoreTimeoutError extends Error {
  readonly code = 'deadline-exceeded'
  constructor() {
    super('Firestore isteği zaman aşımına uğradı')
  }
}

/**
 * Firestore SDK, sunucuya ulaşamadığında (kural reddi değil, ağ/kurulum sorunu)
 * isteği sessizce yeniden denemeye devam eder ve promise hiç çözülmez — arayüz
 * sonsuza dek "yükleniyor" görünür. Bu sarmalayıcı o durumu hataya çevirir.
 */
export function withFirestoreTimeout<T>(
  promise: Promise<T>,
  ms: number = FIRESTORE_TIMEOUT_MS,
): Promise<T> {
  let timer: ReturnType<typeof setTimeout>
  return Promise.race([
    promise,
    new Promise<never>((_, reject) => {
      timer = setTimeout(() => reject(new FirestoreTimeoutError()), ms)
    }),
  ]).finally(() => clearTimeout(timer)) as Promise<T>
}
