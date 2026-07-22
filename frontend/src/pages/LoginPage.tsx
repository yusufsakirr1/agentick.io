import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import AgentLogo from '../components/AgentLogo'
import {
  MessageCircle,
  GitCompareArrows,
  FileUp,
  Database,
  Newspaper,
  BrainCircuit,
  ChevronDown,
  BarChart3,
  Zap,
  Globe,
  LogIn,
  Search,
  Sparkles,
  CheckCircle2,
  Mail,
} from 'lucide-react'

/* ─── Data ─── */

const metrics = [
  { icon: BarChart3, label: '500+ Hisse' },
  { icon: BrainCircuit, label: 'RAG Motoru' },
  { icon: Zap, label: 'Gerçek Zamanlı' },
  { icon: Globe, label: 'Türkçe AI' },
]

const steps = [
  {
    num: '01',
    icon: LogIn,
    title: 'Giriş Yapın',
    desc: 'Google hesabınızla tek tıkla giriş yapın. Ekstra kayıt gerekmez.',
  },
  {
    num: '02',
    icon: Search,
    title: 'Sorunuzu Sorun',
    desc: 'Doğal Türkçe ile istediğiniz hisseyi sorun. AI sorunuzu anlar.',
  },
  {
    num: '03',
    icon: Sparkles,
    title: 'Analiz Alın',
    desc: 'Kaynağa dayalı, detaylı AI yanıtlarını saniyeler içinde alın.',
  },
]

const features = [
  {
    icon: MessageCircle,
    title: 'Yapay Zeka ile Sohbet',
    description:
      'Hisseler hakkında doğal dilde sorular sorun. AI, finansal verileri ve raporları analiz ederek size kapsamlı yanıtlar sunar.',
    color: 'bg-blue-100 text-blue-600',
  },
  {
    icon: GitCompareArrows,
    title: 'Hisse Karşılaştırması',
    description:
      'Birden fazla hisseyi yan yana karşılaştırın. Finansal metrikler, oranlar ve performans göstergeleri ile bilinçli kararlar verin.',
    color: 'bg-green-100 text-green-600',
  },
  {
    icon: FileUp,
    title: 'PDF Yükleme ve Analiz',
    description:
      'Faaliyet raporlarını, bilanço tablolarını ve finansal dokümanları yükleyin. AI otomatik olarak indexleyip analiz eder.',
    color: 'bg-purple-100 text-purple-600',
  },
  {
    icon: Database,
    title: 'Finansal Veri Çekme',
    description:
      'BIST hisselerinin gelir tablosu, bilanço ve nakit akış verilerini tek tıkla çekin ve güncel tutun.',
    color: 'bg-amber-100 text-amber-600',
  },
  {
    icon: Newspaper,
    title: 'Haber Araştırması',
    description:
      'Hisselerle ilgili güncel haberleri otomatik toplayın. AI haberleri analiz edip yatırım kararlarınıza ışık tutar.',
    color: 'bg-rose-100 text-rose-600',
  },
  {
    icon: BrainCircuit,
    title: 'RAG Teknolojisi',
    description:
      'Retrieval-Augmented Generation ile hallüsinasyonsuz, kaynağa dayalı yanıtlar. Her cevabın arkasında gerçek veri var.',
    color: 'bg-indigo-100 text-indigo-600',
  },
]

const faqs = [
  {
    q: 'agentick.io nedir?',
    a: 'agentick.io, BIST hisselerini yapay zeka ile analiz etmenizi sağlayan bir SaaS platformudur. Doğal dilde soru sorarak finansal verilere, raporlara ve haberlere anında erişebilirsiniz.',
  },
  {
    q: 'Hangi verilere erişebilirim?',
    a: 'Platform üzerinden 500\'den fazla BIST hissesinin gelir tablosu, bilanço, nakit akış verileri, faaliyet raporları ve güncel haberlerine erişebilirsiniz.',
  },
  {
    q: 'Ücretsiz mi?',
    a: 'Evet, şu an platform tamamen ücretsizdir. Google hesabınızla giriş yaparak hemen kullanmaya başlayabilirsiniz.',
  },
  {
    q: 'Verilerim güvende mi?',
    a: 'Evet. Firebase Authentication ile güvenli giriş yaparsınız. Verileriniz şifrelenerek saklanır ve üçüncü taraflarla paylaşılmaz.',
  },
  {
    q: 'RAG teknolojisi ne anlama geliyor?',
    a: 'RAG (Retrieval-Augmented Generation), AI\'ın yanıt verirken gerçek verileri kaynak olarak kullanmasını sağlar. Bu sayede hallüsinasyon riski minimuma iner ve her yanıtın arkasında doğrulanabilir veri bulunur.',
  },
]

/* ─── Inline SVG Components ─── */

function HeroChatMockup() {
  return (
    <svg viewBox="0 0 420 340" fill="none" className="w-full h-auto">
      {/* Window frame */}
      <rect width="420" height="340" rx="16" fill="#1a1a2e" />
      {/* Title bar */}
      <rect x="0" y="0" width="420" height="40" rx="16" fill="#16162a" />
      <rect x="0" y="16" width="420" height="24" fill="#16162a" />
      <circle cx="20" cy="20" r="5" fill="#ff5f57" />
      <circle cx="38" cy="20" r="5" fill="#ffbd2e" />
      <circle cx="56" cy="20" r="5" fill="#28c840" />
      <text x="210" y="24" textAnchor="middle" fill="#8888aa" fontSize="12" fontFamily="Inter, sans-serif">
        agentick.io — AI Chat
      </text>

      {/* User message */}
      <rect x="120" y="65" width="280" height="48" rx="12" fill="#3b82f6" />
      <text x="140" y="85" fill="white" fontSize="12.5" fontFamily="Inter, sans-serif">
        THYAO'nun son çeyrek gelir
      </text>
      <text x="140" y="101" fill="white" fontSize="12.5" fontFamily="Inter, sans-serif">
        tablosunu analiz eder misin?
      </text>

      {/* AI avatar + response */}
      <circle cx="36" cy="148" r="14" fill="#6366f1" />
      <text x="36" y="152" textAnchor="middle" fill="white" fontSize="11" fontWeight="bold" fontFamily="Inter, sans-serif">
        AI
      </text>
      <rect x="60" y="128" width="320" height="96" rx="12" fill="#222240" />
      <text x="78" y="152" fill="#e0e0ff" fontSize="12" fontFamily="Inter, sans-serif">
        THYAO 2024 Q4 Gelir Tablosu:
      </text>
      <text x="78" y="170" fill="#a0a0cc" fontSize="11" fontFamily="Inter, sans-serif">
        Hasılat: 287.4 Milyar TL (+18%)
      </text>
      <text x="78" y="187" fill="#a0a0cc" fontSize="11" fontFamily="Inter, sans-serif">
        Net Kar: 42.1 Milyar TL (+12%)
      </text>
      <text x="78" y="204" fill="#a0a0cc" fontSize="11" fontFamily="Inter, sans-serif">
        FAVÖK Marjı: %22.3
      </text>

      {/* User second message */}
      <rect x="160" y="248" width="240" height="36" rx="12" fill="#3b82f6" />
      <text x="180" y="271" fill="white" fontSize="12.5" fontFamily="Inter, sans-serif">
        Peki PGSUS ile karşılaştır
      </text>

      {/* Typing indicator */}
      <circle cx="36" cy="310" r="14" fill="#6366f1" />
      <text x="36" y="314" textAnchor="middle" fill="white" fontSize="11" fontWeight="bold" fontFamily="Inter, sans-serif">
        AI
      </text>
      <rect x="60" y="298" width="80" height="28" rx="10" fill="#222240" />
      <circle cx="80" cy="312" r="3" fill="#8888cc">
        <animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" repeatCount="indefinite" />
      </circle>
      <circle cx="94" cy="312" r="3" fill="#8888cc">
        <animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" begin="0.2s" repeatCount="indefinite" />
      </circle>
      <circle cx="108" cy="312" r="3" fill="#8888cc">
        <animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" begin="0.4s" repeatCount="indefinite" />
      </circle>
    </svg>
  )
}

function AppPreviewMockup() {
  return (
    <svg viewBox="0 0 480 320" fill="none" className="w-full h-auto">
      {/* Browser frame */}
      <rect width="480" height="320" rx="12" fill="#f3f4f6" stroke="#e5e7eb" strokeWidth="1" />
      {/* Title bar */}
      <rect x="0" y="0" width="480" height="36" rx="12" fill="#ffffff" />
      <rect x="0" y="12" width="480" height="24" fill="#ffffff" />
      <line x1="0" y1="36" x2="480" y2="36" stroke="#e5e7eb" strokeWidth="1" />
      <circle cx="18" cy="18" r="4.5" fill="#ff5f57" />
      <circle cx="34" cy="18" r="4.5" fill="#ffbd2e" />
      <circle cx="50" cy="18" r="4.5" fill="#28c840" />
      {/* URL bar */}
      <rect x="80" y="9" width="320" height="18" rx="4" fill="#f3f4f6" />
      <text x="240" y="21" textAnchor="middle" fill="#9ca3af" fontSize="9" fontFamily="Inter, sans-serif">
        app.agentick.io
      </text>

      {/* Sidebar */}
      <rect x="0" y="36" width="100" height="284" fill="#f9fafb" />
      <rect x="0" y="296" width="100" height="24" rx="0" fill="#f9fafb" />
      <rect x="12" y="52" width="76" height="8" rx="4" fill="#e5e7eb" />
      <rect x="12" y="72" width="76" height="24" rx="6" fill="#3b82f6" />
      <text x="50" y="88" textAnchor="middle" fill="white" fontSize="8" fontFamily="Inter, sans-serif">
        Chat
      </text>
      <rect x="12" y="104" width="76" height="24" rx="6" fill="#ffffff" stroke="#e5e7eb" strokeWidth="0.5" />
      <text x="50" y="120" textAnchor="middle" fill="#6b7280" fontSize="8" fontFamily="Inter, sans-serif">
        Karşılaştır
      </text>

      {/* Chat area */}
      <rect x="112" y="48" width="356" height="260" rx="8" fill="#ffffff" />
      {/* Messages */}
      <rect x="220" y="62" width="236" height="28" rx="8" fill="#3b82f6" />
      <text x="240" y="80" fill="white" fontSize="9.5" fontFamily="Inter, sans-serif">
        EREGL bilanço özeti ver
      </text>
      <rect x="124" y="100" width="280" height="56" rx="8" fill="#f3f4f6" />
      <text x="136" y="118" fill="#374151" fontSize="9" fontFamily="Inter, sans-serif">
        EREGL 2024 Bilanço Özeti:
      </text>
      <text x="136" y="132" fill="#6b7280" fontSize="8.5" fontFamily="Inter, sans-serif">
        Toplam Varlıklar: 142.8 Milyar TL
      </text>
      <text x="136" y="145" fill="#6b7280" fontSize="8.5" fontFamily="Inter, sans-serif">
        Özkaynaklar: 98.2 Milyar TL
      </text>

      {/* Input bar */}
      <rect x="112" y="278" width="356" height="30" rx="8" fill="#f9fafb" stroke="#e5e7eb" strokeWidth="0.5" />
      <text x="130" y="297" fill="#9ca3af" fontSize="9" fontFamily="Inter, sans-serif">
        Bir soru sorun...
      </text>
    </svg>
  )
}

/* ─── Main Page ─── */

export default function LoginPage() {
  const { signInWithGoogle } = useAuth()
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  const heading = (extra = '') =>
    `font-family: 'League Spartan', sans-serif; font-weight: 700; ${extra}`

  return (
    <div className="min-h-screen bg-white">
      {/* ── 1. Navbar ── */}
      <nav className="fixed top-0 inset-x-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-1 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <AgentLogo size={36} />
            <span
              style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
              className="text-lg text-gray-900 leading-none tracking-tight -ml-1"
            >
              agentick.io
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={signInWithGoogle}
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors cursor-pointer"
            >
              Giriş Yap
            </button>
            <button
              onClick={signInWithGoogle}
              className="text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 px-5 py-2 rounded-full transition-colors cursor-pointer"
            >
              Ücretsiz Başla
            </button>
          </div>
        </div>
      </nav>

      {/* ── 2. Hero Section ── */}
      <section className="relative min-h-screen flex items-center overflow-hidden pt-16">
        {/* Decorative blobs */}
        <div className="absolute top-20 -left-32 w-96 h-96 bg-blue-200 rounded-full opacity-20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-0 w-80 h-80 bg-purple-200 rounded-full opacity-20 blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-100 rounded-full opacity-10 blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 w-full grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center relative z-10">
          {/* Left */}
          <div>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-50 border border-green-100 text-sm text-green-700 mb-8">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Yapay zeka destekli BIST analiz platformu
            </div>

            <h1
              style={{ fontFamily: "'League Spartan', sans-serif" }}
              className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 leading-[1.08] tracking-tight mb-6"
            >
              BIST Hisselerini{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                Yapay Zeka
              </span>{' '}
              ile Analiz Edin
            </h1>

            <p className="text-lg sm:text-xl text-gray-500 max-w-lg mb-10 leading-relaxed">
              Finansal verileri sorgulayın, raporları analiz edin ve hisselerinizi
              karşılaştırın — hepsi tek bir AI asistanla. Doğal Türkçe ile sorun,
              anında yanıt alın.
            </p>

            <div className="flex flex-wrap items-center gap-4">
              <button
                onClick={signInWithGoogle}
                className="text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 px-8 py-3.5 rounded-full transition-colors cursor-pointer shadow-lg shadow-gray-900/10"
              >
                Ücretsiz Başlayın
              </button>
              <button
                onClick={() => scrollTo('how-it-works')}
                className="text-sm font-medium text-gray-700 border border-gray-200 hover:bg-gray-50 px-8 py-3.5 rounded-full transition-colors cursor-pointer"
              >
                Nasıl Çalışır?
              </button>
            </div>
          </div>

          {/* Right — Chat Mockup */}
          <div className="relative">
            <div className="rounded-2xl shadow-2xl shadow-gray-900/10 overflow-hidden">
              <HeroChatMockup />
            </div>
          </div>
        </div>
      </section>

      {/* ── 3. Trust Strip ── */}
      <section className="bg-gray-50 py-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
            {metrics.map((m) => (
              <div key={m.label} className="flex items-center gap-3 justify-center">
                <div className="w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center">
                  <m.icon size={20} className="text-gray-700" strokeWidth={1.8} />
                </div>
                <span className="text-sm font-semibold text-gray-700">{m.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 4. Nasıl Çalışır? ── */}
      <section id="how-it-works" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <h2
            style={{ fontFamily: "'League Spartan', sans-serif" }}
            className="text-3xl sm:text-4xl font-bold text-gray-900 text-center mb-4 tracking-tight"
          >
            Nasıl Çalışır?
          </h2>
          <p className="text-gray-500 text-center mb-16 max-w-lg mx-auto">
            Üç basit adımda yapay zeka destekli finansal analize başlayın.
          </p>

          <div className="relative grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-6">
            {/* Dashed connector line — desktop only */}
            <div className="hidden md:block absolute top-14 left-[20%] right-[20%] border-t-2 border-dashed border-gray-200 pointer-events-none" />

            {steps.map((s) => (
              <div key={s.num} className="relative text-center">
                <div className="mx-auto w-28 h-28 rounded-full bg-gray-50 border-2 border-gray-100 flex flex-col items-center justify-center mb-6 relative z-10">
                  <span
                    style={{ fontFamily: "'League Spartan', sans-serif" }}
                    className="text-xs font-bold text-gray-400 mb-1"
                  >
                    {s.num}
                  </span>
                  <s.icon size={28} className="text-gray-900" strokeWidth={1.6} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500 max-w-xs mx-auto leading-relaxed">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 5. Features ── */}
      <section id="features" className="bg-gray-50 py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <h2
            style={{ fontFamily: "'League Spartan', sans-serif" }}
            className="text-3xl sm:text-4xl font-bold text-gray-900 text-center mb-4 tracking-tight"
          >
            Her şeyi tek platformda yapın
          </h2>
          <p className="text-gray-500 text-center mb-16 max-w-lg mx-auto">
            Finansal analiz için ihtiyacınız olan tüm araçlar, yapay zeka ile güçlendirilmiş şekilde elinizin altında.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="bg-white rounded-2xl p-8 hover:shadow-lg transition-shadow duration-300"
              >
                <div className={`w-12 h-12 rounded-xl ${f.color} flex items-center justify-center mb-5`}>
                  <f.icon size={22} strokeWidth={1.8} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 6. Platform Preview ── */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left — Text */}
          <div>
            <h2
              style={{ fontFamily: "'League Spartan', sans-serif" }}
              className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6 tracking-tight"
            >
              Platformu keşfedin
            </h2>
            <p className="text-gray-500 mb-8 leading-relaxed">
              Modern ve sade arayüzümüzle finansal verilerinize anında erişin.
              Tek bir ekrandan tüm analizlerinizi yönetin.
            </p>
            <ul className="space-y-4 mb-10">
              {[
                'Doğal dilde soru-cevap arayüzü',
                'Çoklu hisse karşılaştırma paneli',
                'Otomatik veri güncelleme',
                'PDF rapor yükleme ve analiz',
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <CheckCircle2 size={20} className="text-green-500 mt-0.5 flex-shrink-0" strokeWidth={2} />
                  <span className="text-sm text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={signInWithGoogle}
              className="text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 px-7 py-3 rounded-full transition-colors cursor-pointer"
            >
              Denemek için ücretsiz başlayın
            </button>
          </div>

          {/* Right — App Preview */}
          <div className="rounded-2xl shadow-xl shadow-gray-200/60 overflow-hidden border border-gray-100">
            <AppPreviewMockup />
          </div>
        </div>
      </section>

      {/* ── 7. FAQ ── */}
      <section className="bg-gray-50 py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <h2
            style={{ fontFamily: "'League Spartan', sans-serif" }}
            className="text-3xl sm:text-4xl font-bold text-gray-900 text-center mb-4 tracking-tight"
          >
            Sıkça Sorulan Sorular
          </h2>
          <p className="text-gray-500 text-center mb-12">
            Merak ettiklerinizin yanıtları burada.
          </p>

          <div className="space-y-3">
            {faqs.map((faq, i) => {
              const isOpen = openFaq === i
              return (
                <div
                  key={i}
                  className="bg-white rounded-xl border border-gray-100 overflow-hidden transition-shadow hover:shadow-sm"
                >
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : i)}
                    className="w-full flex items-center justify-between px-6 py-5 text-left cursor-pointer"
                  >
                    <span className="text-sm font-semibold text-gray-900">{faq.q}</span>
                    <ChevronDown
                      size={18}
                      className={`text-gray-400 transition-transform duration-200 flex-shrink-0 ml-4 ${
                        isOpen ? 'rotate-180' : ''
                      }`}
                    />
                  </button>
                  <div
                    className={`overflow-hidden transition-all duration-200 ${
                      isOpen ? 'max-h-60 pb-5' : 'max-h-0'
                    }`}
                  >
                    <p className="px-6 text-sm text-gray-500 leading-relaxed">{faq.a}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── 8. Final CTA ── */}
      <section className="bg-gray-900 py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2
            style={{ fontFamily: "'League Spartan', sans-serif" }}
            className="text-3xl sm:text-4xl font-bold text-white mb-6 tracking-tight"
          >
            Yapay zeka destekli analize hemen başlayın
          </h2>
          <p className="text-gray-400 mb-10 max-w-lg mx-auto leading-relaxed">
            Ücretsiz hesabınızı oluşturun ve BIST hisselerinizi AI ile analiz
            etmeye bugün başlayın. Kredi kartı gerekmez.
          </p>
          <button
            onClick={signInWithGoogle}
            className="text-sm font-medium text-gray-900 bg-white hover:bg-gray-100 px-8 py-3.5 rounded-full transition-colors cursor-pointer shadow-lg"
          >
            Google ile Ücretsiz Başlayın
          </button>
        </div>
      </section>

      {/* ── 9. Footer ── */}
      <footer className="border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-1 mb-4">
                <AgentLogo size={32} />
                <span
                  style={{ fontFamily: "'League Spartan', sans-serif", fontWeight: 500 }}
                  className="text-base text-gray-900 leading-none tracking-tight -ml-0.5"
                >
                  agentick.io
                </span>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed max-w-xs">
                Yapay zeka destekli BIST analiz platformu. Doğal dilde soru
                sorun, anında finansal analiz alın.
              </p>
            </div>

            {/* Product links */}
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-4">Ürün</h4>
              <ul className="space-y-3">
                {[
                  { label: 'AI Sohbet', id: 'features' },
                  { label: 'Hisse Karşılaştırma', id: 'features' },
                  { label: 'Nasıl Çalışır?', id: 'how-it-works' },
                  { label: 'SSS', id: 'faq' },
                ].map((link) => (
                  <li key={link.label}>
                    <button
                      onClick={() => scrollTo(link.id)}
                      className="text-sm text-gray-500 hover:text-gray-900 transition-colors cursor-pointer"
                    >
                      {link.label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-4">İletişim</h4>
              <ul className="space-y-3">
                <li className="flex items-center gap-2 text-sm text-gray-500">
                  <Mail size={16} strokeWidth={1.8} />
                  info@agentick.io
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-100">
          <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
            <span className="text-xs text-gray-400">&copy; 2026 agentick.io. Tüm hakları saklıdır.</span>
            <span className="text-xs text-gray-400">Istanbul, Türkiye</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
