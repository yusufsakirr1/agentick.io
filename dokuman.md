# agentick.io — Oturum Notu

Bu dosya, Claude Code ile yapılan çalışmaların özetini tutar.
Her oturuma bu dosyayı atarak nereden devam edeceğimizi belirleriz.

---

## Proje Özeti

**Ürün:** BIST hisseleri için Türkçe AI finansal analist (agentick.io)
**Hedef kitle:** Temel analiz yapmaya çalışan Türk bireysel yatırımcısı
**İş modeli:** Freemium SaaS — 5 sorgu ücretsiz, sonrası aylık ücret
**Rekabet avantajı:** Yapılandırılmış finansal veri (yfinance) + KAP PDF + haber + agentic reasoning + Türkçe

---

## Teknoloji Stack

| Katman | Teknoloji | Durum |
|---|---|---|
| LLM (Sentez) | Claude Sonnet 4.6 | Aktif |
| LLM (Planner/Critic/SQL) | Claude Haiku 4.5 | Aktif |
| Agent Orkestrasyonu | LangGraph | Aktif |
| Embedding | paraphrase-multilingual-mpnet-base-v2 (lokal) | Aktif |
| Vektör DB | Qdrant Cloud (EU-Central-1) | Aktif |
| İlişkisel DB | SQLite | Aktif |
| Finansal Veri | yfinance | Aktif |
| PDF İşleme | pdfplumber (tablolar) + PyMuPDF (metin) | Aktif |
| Auth | Firebase Authentication (Google OAuth) | Aktif |
| Backend | FastAPI + Uvicorn | Aktif |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS | Aktif |
| Routing (Frontend) | react-router-dom v7 | Aktif |
| İkonlar | lucide-react | Aktif |
| Gözlemlenebilirlik | LangSmith | Aktif |
| Test | pytest + pytest-asyncio (14 test) | Aktif |
| CI/CD | GitHub Actions (test + build) | Aktif |
| Logging | Python logging modülü (structured) | Aktif |

---

## Klasör Yapısı

```
agentick.io/
├── backend/
│   ├── main.py                   # FastAPI app + logging config
│   ├── auth.py                   # Firebase Auth + dev mode bypass (production-safe)
│   ├── routes/
│   │   ├── upload.py             # POST /api/upload (ticker whitelist, 50MB limit, safe filename)
│   │   ├── query.py              # POST /api/ask (120s timeout)
│   │   ├── fetch_data.py         # POST /api/fetch-data (60s timeout)
│   │   ├── fetch_news.py         # POST /api/fetch-news
│   │   ├── compare.py            # GET /api/compare/metrics, POST /api/compare/ask (timeout + try/finally)
│   │   └── portfolio.py          # POST /api/portfolio/metrics, ask, news (timeout + try/finally)
│   └── services/
│       ├── pdf_pipeline.py       # PDF → SQLite + Qdrant
│       └── metrics_utils.py      # Paylaşılan metrik helper'lar (compare + portfolio)
├── src/
│   ├── agent/
│   │   ├── state.py              # AgentState (tickers alanı dahil)
│   │   ├── planner_node.py       # Tek + çoklu ticker prompt'ları
│   │   ├── router_node.py        # Auto-fetch + per-task ticker + timeout
│   │   ├── critic_node.py
│   │   ├── synthesizer_node.py   # Tek + karşılaştırma prompt'ları
│   │   └── graph.py              # run_agent(question, ticker, history, tickers)
│   ├── retrievers/
│   │   ├── sql_retriever.py      # Text-to-SQL (SQLite, 8 tablo)
│   │   ├── vector_retriever.py   # Qdrant semantic search (singleton, thread-safe, hata toleranslı)
│   │   └── news_retriever.py     # Haber arama (AND keyword)
│   └── ingestion/
│       ├── bist_finance_client.py  # yfinance → SQLite (temettü + bedelsiz + sektör dahil)
│       ├── news_client.py          # RSS haber çekme (AND keyword arama)
│       ├── pdf_chunker.py          # PDF → text chunks
│       └── build_vector_index.py   # chunks → Qdrant
├── frontend/
│   └── src/
│       ├── main.tsx              # BrowserRouter + AuthProvider sarma
│       ├── App.tsx               # Auth guard + Layout shell + Routes
│       ├── config/
│       │   └── firebase.ts       # Firebase config + GoogleAuthProvider
│       ├── contexts/
│       │   └── AuthContext.tsx    # Firebase Auth context (signInWithGoogle, signOut)
│       ├── constants/
│       │   └── tickers.ts        # BIST-30 tek kaynak
│       ├── pages/
│       │   ├── LoginPage.tsx       # Landing page (9 bölüm, inline SVG mockup'lar)
│       │   ├── ChatPage.tsx        # Sohbet sayfası
│       │   ├── ComparePage.tsx     # Karşılaştırma sayfası
│       │   └── PortfolioPage.tsx   # Portföy dashboard sayfası
│       ├── components/
│       │   ├── AgentLogo.tsx       # Marka logosu (lucide MousePointerClick)
│       │   ├── Sidebar.tsx         # Sohbet/Karşılaştır/Portföy navigasyonu
│       │   ├── ChatInput.tsx
│       │   ├── Message.tsx
│       │   ├── ThinkingIndicator.tsx
│       │   ├── TickerSelector.tsx          # Multi-select ticker seçici
│       │   ├── ComparisonTable.tsx         # Metrik tablosu
│       │   ├── ComparisonChat.tsx          # Karşılaştırma Q&A
│       │   ├── PortfolioManager.tsx        # Holding ekleme/çıkarma
│       │   ├── PortfolioSummaryCards.tsx   # 6 özet kart (değer, K/Z, F/K, temettü)
│       │   ├── SectorChart.tsx            # CSS bar chart (sektör dağılımı)
│       │   ├── ConcentrationWarnings.tsx   # Konsantrasyon risk uyarıları
│       │   ├── PortfolioHoldingsTable.tsx  # Detay tablosu (9 kolon)
│       │   ├── DividendCalendar.tsx        # Temettü takvimi (Türkçe tarih)
│       │   ├── PortfolioNews.tsx           # Portföy haberleri
│       │   └── PortfolioChat.tsx           # Portföy AI soru-cevap
│       ├── api/
│       │   └── client.ts       # fetchComparisonMetrics, askCompareQuestion, fetchPortfolioMetrics dahil
│       └── services/
│           ├── conversationStorage.ts
│           └── portfolioService.ts   # Firestore portföy CRUD
├── tests/
│   ├── conftest.py               # Shared fixtures (TestClient + auth bypass)
│   ├── test_health.py            # Health endpoint testi
│   ├── test_auth.py              # Auth middleware testleri (dev mode + production mode)
│   └── test_validation.py        # 12 input validation testi
├── .github/
│   └── workflows/
│       └── ci.yml                # CI/CD: pytest + frontend build
├── data/
│   ├── raw/                      # Yüklenen PDF'ler
│   └── bist_financials.db        # SQLite
├── docs/
│   └── assets/
│       └── chat-ui.png           # UI ekran görüntüsü
├── pyproject.toml                # uv + pytest config (dev extras)
├── .env.example                  # Backend ortam değişkenleri şablonu
└── frontend/.env.example         # Frontend Firebase config şablonu
```

---

## Tamamlanan Fazlar

| Faz | İçerik | Durum |
|---|---|---|
| 1 | Veri Katmanı + Naive RAG (PDF → Qdrant → CLI cevap) | ✅ |
| 2 | SQL Retriever (yfinance + SQLite + text-to-SQL) | ✅ |
| 3 | LangGraph Agent + FastAPI + React Frontend | ✅ |
| 3.5 | Haber Retriever + Temettü + Auto-fetch | ✅ |
| 4 | Çoklu Şirket Karşılaştırma | ✅ |
| 5 | Firebase Auth + Landing Page Yeniden Tasarım | ✅ |
| 6 | Portföy Dashboard + Bedelsiz Sermaye Artırımı | ✅ |
| Sprint 1 | Güvenlik Sertleştirme (API key temizliği, auth fix, timeout, connection leak) | ✅ |
| Sprint 2 | Test Altyapısı + CI/CD + Logging + Input Validation | ✅ |

---

## Son Durum (Sprint 2 sonrası)

### Çalışan Özellikler
- LangGraph agent: Planner → Router → Critic → Synthesizer döngüsü
- 3 retriever paralel: SQL + Vektör + Haber
- 8 SQLite tablosu: income_statement, balance_sheet, cash_flow, ratios, dividends, stock_splits, pdf_tables, news_articles
- Temettü verisi (yfinance .dividends) + temettü verimi hesaplama (dividends JOIN ratios)
- **Bedelsiz sermaye artırımı:** stock_splits tablosu (yfinance .splits), SQL Retriever şemasında tanımlı
- **Sektör verisi:** ratios tablosunda `sector` kolonu (yfinance info.sector)
- **Auto-fetch:** SQL boş dönünce otomatik yfinance'den çekip tekrar sorgulama
- PDF upload → tablo çıkarma + metin indexleme + yfinance güncelleme
- Sohbet hafızası (localStorage + API)
- BIST-30 tam destek
- LangSmith tracing
- **Çoklu şirket karşılaştırma:** `/compare` sayfasında 2 hisseyi yan yana karşılaştırma
- **Metrik tablosu:** Fiyat, F/K, PD/DD, net marj, ROE, ROA, temettü verimi, gelir, net kâr vb. — LLM gerektirmeyen doğrudan SQLite sorgusu
- **Karşılaştırma chat:** Seçili hisseler hakkında serbest soru-cevap (multi-ticker agent)
- **React Router:** `/` (sohbet), `/compare` (karşılaştırma), `/portfolio` (portföy) sayfaları
- **Sidebar navigasyonu:** Sohbet / Karşılaştır / Portföy sekmeli geçiş
- **Firebase Auth:** Google OAuth ile giriş, AuthContext + AuthProvider pattern
- **Landing Page:** 9 bölümlük profesyonel SaaS sayfası — Navbar, Hero (inline SVG chat mockup), Trust Strip, Nasıl Çalışır (3 adım), Özellikler (6 renkli kart), Platform Önizleme (browser frame SVG), FAQ Accordion (5 soru, useState toggle), Koyu CTA Banner, Detaylı Footer
- **Auth Guard:** `App.tsx`'te `!user` kontrolü → LoginPage gösterimi, giriş sonrası otomatik yönlendirme
- **Portföy Dashboard:** Firestore'da portföy saklama, per-holding metrikler, sektör dağılımı (CSS bar chart), konsantrasyon uyarıları, temettü takvimi (Türkçe tarih), portföy haberleri, AI soru-cevap
- **Haber arama iyileştirmesi:** OR → AND keyword araması (alakasız haber önleme)

### Güvenlik ve Kalite (Sprint 1 + Sprint 2)
- **API key temizliği:** git geçmişinden `.env` dosyaları `git filter-repo` ile silindi, tüm API key'ler rotate edildi
- **Firebase Auth production-safe:** Production'da `FIREBASE_PRIVATE_KEY` yoksa `RuntimeError` fırlatır, hata mesajından internal detay sızması engellendi
- **Qdrant hata toleransı:** Singleton client (thread-safe), bağlantı hatalarında boş liste döner (crash etmez)
- **API timeout'ları:** Agent çağrıları 120s, yfinance fetch 60s (`asyncio.wait_for`)
- **DB bağlantı leak önleme:** Tüm SQLite bağlantıları `try/finally` ile kapatılır
- **Input validation:** BIST-30 ticker whitelist (30 hisse), 50MB dosya boyutu limiti, sadece PDF kabul, güvenli dosya adı regex, tüm endpoint'lerde `HTTPException`
- **Structured logging:** Tüm `print()` ifadeleri `logging` modülüne migrate edildi (INFO/WARNING/ERROR seviyeleri)
- **Test altyapısı:** 14 pytest testi — health endpoint, auth middleware (dev + production), 12 input validation testi
- **CI/CD pipeline:** GitHub Actions — her push/PR'da backend testleri + frontend TypeScript check + build
- **`.env.example` şablonları:** Backend ve frontend için ortam değişkeni şablonları

### API Endpoint'leri

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/upload/sync` | PDF yükle ve indexle (ticker whitelist + 50MB limit) |
| POST | `/api/ask` | Soru sor, agent yanıtını al (120s timeout) |
| POST | `/api/fetch-data` | yfinance verisini SQLite'a çek (60s timeout) |
| POST | `/api/fetch-news` | Haber verilerini çek |
| GET | `/api/compare/metrics` | 2 ticker için metrik karşılaştırması (yfinance auto-fetch dahil) |
| POST | `/api/compare/ask` | Karşılaştırma sorusu sor (multi-ticker agent, 120s timeout) |
| POST | `/api/portfolio/metrics` | Portföy metrikleri, sektör dağılımı, uyarılar, temettü takvimi |
| POST | `/api/portfolio/ask` | Portföy hakkında AI soru-cevap (multi-ticker agent, 120s timeout) |
| POST | `/api/portfolio/news` | Portföy hisselerine ait haberler |
| GET | `/api/health` | Sağlık kontrolü |

---

## Gelecek Çalışmalar

Aşağıdaki özellikler sistemin ChatGPT'ye PDF yüklemekten **gerçek farkını** ortaya koyacak ve monetize edilebilir hale getirecek geliştirmelerdir.

### 1. Otomatik Screening ve Alert
Kullanıcının belirlediği kriterlere göre hisse taraması ve bildirim. Örnek:
- "Temettü verimi %5 üzeri, borç/özkaynak %50 altı BIST hisseleri bul"
- "P/E oranı 10'un altındaki hisseler"
- "Net marjı son 2 yılda artan şirketler"

**Gerekli:** Tüm BIST-30 hisseleri için periyodik veri çekme (cron/scheduler), screening query engine.

### 2. Zaman Serisi Takibi ve Bildirim
Hisse takibi ve önemli olay bildirimi. Örnek:
- "TUPRS'u takip et, temettü açıklanınca bildir"
- "THYAO fiyatı 350 TL'yi geçerse uyar"
- "Takip listeme ASELS ve FROTO ekle"

**Gerekli:** Kullanıcı bazlı watchlist, background scheduler, push notification (email/webhook).

### ~~3. Portföy Analizi~~ ✅ Faz 6'da tamamlandı
Portföy dashboard: Firestore'da holding CRUD, sektör dağılımı, konsantrasyon uyarıları, ağırlıklı metrikler, temettü takvimi, haber akışı, AI soru-cevap.

### 4. BIST'e Özel Domain Bilgisi ve KAP Entegrasyonu
ChatGPT genel amaçlı — agentick BIST'e özel. Fark yaratan özellikler:
- KAP özel durum açıklamaları (temettü, sermaye artırımı, birleşme) otomatik çekme
- BIST endeks değişiklikleri takibi
- Türk muhasebe standartlarına göre rasyo hesaplama
- Halka arz takibi

**Gerekli:** KAP veri dağıtım sözleşmesi veya alternatif veri kaynakları (Finnet, Matriks, İş Yatırım API).

### 5. Ürünleştirme ve Deployment
- Dockerfile + docker-compose (backend + frontend)
- Rate limiting (kullanıcı başına sorgu limiti)
- CORS restriction (production domain'e sınırlama)
- Swagger/OpenAPI dökümantasyonu
- Kullanıcı başına aylık sorgu kotası (Firestore)
- Deployment — Railway (backend) + Vercel (frontend)
- Eval sistemi — 30 BIST sorusu ile doğruluk metrikleri
- Stripe entegrasyonu — ₺199/ay abonelik

---

## Devam Edilecek Yer

Sprint 1 ve Sprint 2 tamamlandı. Tüm güvenlik sertleştirmeleri, test altyapısı, CI/CD pipeline ve structured logging yerinde. Sıradaki en yüksek değerli adım **Deployment** (Railway + Vercel) ile canlıya alma, ardından **Otomatik Screening** özelliği.
