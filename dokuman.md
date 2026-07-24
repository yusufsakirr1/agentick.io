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

---

## Klasör Yapısı

```
agentick.io/
├── backend/
│   ├── main.py
│   ├── auth.py                 # Firebase Auth + dev mode bypass
│   ├── routes/
│   │   ├── upload.py           # POST /api/upload
│   │   ├── query.py            # POST /api/ask
│   │   ├── fetch_data.py       # POST /api/fetch-data
│   │   ├── fetch_news.py       # POST /api/fetch-news
│   │   ├── compare.py          # GET /api/compare/metrics, POST /api/compare/ask
│   │   └── portfolio.py        # POST /api/portfolio/metrics, ask, news
│   └── services/
│       ├── pdf_pipeline.py     # PDF → SQLite + Qdrant
│       └── metrics_utils.py    # Paylaşılan metrik helper'lar (compare + portfolio)
├── src/
│   ├── agent/
│   │   ├── state.py            # AgentState (tickers alanı dahil)
│   │   ├── planner_node.py     # Tek + çoklu ticker prompt'ları
│   │   ├── router_node.py      # Auto-fetch + per-task ticker + timeout
│   │   ├── critic_node.py
│   │   ├── synthesizer_node.py # Tek + karşılaştırma prompt'ları
│   │   └── graph.py            # run_agent(question, ticker, history, tickers)
│   ├── retrievers/
│   │   ├── sql_retriever.py    # Text-to-SQL (SQLite)
│   │   ├── vector_retriever.py # Qdrant semantic search (15s timeout)
│   │   └── news_retriever.py   # Haber arama
│   └── ingestion/
│       ├── bist_finance_client.py  # yfinance → SQLite (temettü + bedelsiz + sektör dahil)
│       ├── news_client.py          # RSS haber çekme (AND keyword arama)
│       ├── pdf_chunker.py          # PDF → text chunks
│       └── build_vector_index.py   # chunks → Qdrant
├── frontend/
│   └── src/
│       ├── main.tsx            # BrowserRouter + AuthProvider sarma
│       ├── App.tsx             # Auth guard + Layout shell + Routes
│       ├── config/
│       │   └── firebase.ts     # Firebase config + GoogleAuthProvider
│       ├── contexts/
│       │   └── AuthContext.tsx  # Firebase Auth context (signInWithGoogle, signOut)
│       ├── constants/
│       │   └── tickers.ts      # BIST-30 tek kaynak
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
├── data/
│   ├── raw/                    # Yüklenen PDF'ler
│   └── bist_financials.db      # SQLite
├── pyproject.toml
└── .env
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

---

## Son Durum (Faz 6 sonrası)

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

### API Endpoint'leri

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/upload/sync` | PDF yükle ve indexle |
| POST | `/api/ask` | Soru sor, agent yanıtını al |
| POST | `/api/fetch-data` | yfinance verisini SQLite'a çek |
| POST | `/api/fetch-news` | Haber verilerini çek |
| GET | `/api/compare/metrics` | 2 ticker için metrik karşılaştırması (yfinance auto-fetch dahil) |
| POST | `/api/compare/ask` | Karşılaştırma sorusu sor (multi-ticker agent) |
| POST | `/api/portfolio/metrics` | Portföy metrikleri, sektör dağılımı, uyarılar, temettü takvimi |
| POST | `/api/portfolio/ask` | Portföy hakkında AI soru-cevap (multi-ticker agent) |
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
- Kullanıcı başına aylık sorgu kotası (Firestore)
- Deployment — Railway (backend) + Vercel (frontend)
- Eval sistemi — 30 BIST sorusu ile doğruluk metrikleri
- Stripe entegrasyonu — ₺199/ay abonelik

---

## Devam Edilecek Yer

Portföy dashboard tamamlandı. Sıradaki en yüksek değerli özellik **Otomatik Screening** — tüm BIST-30 için periyodik veri çekme ve kullanıcının belirlediği kriterlere göre hisse taraması. Ardından **Deployment** (Railway + Vercel) ile canlıya alınabilir.
