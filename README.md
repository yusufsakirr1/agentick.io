<p align="center">
  <img src="docs/assets/chat-ui.png" alt="agentick.io — AI Finansal Analist" width="700" />
</p>

<h1 align="center">agentick.io</h1>

<p align="center">
  <strong>BIST hisseleri icin Turkce AI finansal analist</strong><br/>
  Agentic RAG · LangGraph · Claude · Qdrant · FastAPI · React
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" alt="React" />
  <img src="https://img.shields.io/badge/LLM-Claude%20Haiku%204.5-blueviolet" alt="Claude" />
  <img src="https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions" alt="CI" />
  <img src="https://img.shields.io/badge/Tests-73%20passing-brightgreen" alt="Tests" />
</p>

---

## Ne Yapar?

Turk bireysel yatirimcilarin BIST hisseleri uzerinde **Turkce sorular** sorabilecegi, **kaynakli ve guvenilir** cevaplar aldigi yapay zeka destekli finansal analiz platformu.

- KAP faaliyet raporlari (PDF) yukleyin, yapay zeka tabloyu ve metni anlasin
- yfinance ile canli finansal veriler (gelir tablosu, bilanco, nakit akisi, oranlar)
- Hisseler arasi karsilastirma (F/K, PD/DD, net marj, ROE vb.)
- Portfoy dashboard (K/Z, sektor dagilimi, temettu takvimi, konsantrasyon uyarilari)
- Haberleri takip edin (RSS -- su an Bloomberg HT)

---

## Mimari

```
Kullanici sorusu
      |
      v
  PLANNER (Claude Haiku)  --> soruyu alt gorevlere boler
      |
      v
  ROUTER (asyncio.gather) --> paralel retriever cagrisi
      |
      +-- SQL Retriever      (yfinance + PDF tablolari -- SQLite)
      |                       └── bos donerse --> auto-fetch --> tekrar sorgula
      +-- Vector Retriever   (KAP rapor metni -- Qdrant)
      +-- News Retriever     (RSS haberler -- SQLite)
      |
      v
  CRITIC (Claude Haiku)    --> bilgi yeterli mi? degilse PLANNER'a geri don (max 3 tur)
      |
      v
  SYNTHESIZER (Claude Haiku 4.5) --> Turkce, kaynakli cevap
```

---

## Teknoloji Stack

| Katman | Teknoloji |
|---|---|
| LLM (tum node'lar) | Claude Haiku 4.5 |
| Agent Orkestrasyonu | LangGraph |
| Embedding | paraphrase-multilingual-mpnet-base-v2 (lokal, 768D) |
| Vektor DB | Qdrant Cloud (EU-Central-1) |
| Iliskisel DB | SQLite |
| Finansal Veri | yfinance |
| PDF Isleme | pdfplumber (tablolar) + PyMuPDF (metin) |
| Auth | Firebase Authentication (Google OAuth) |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Test | pytest + pytest-asyncio (73 test) |
| CI/CD | GitHub Actions (backend test + frontend build) |
| Gozlemlenebilirlik | LangSmith |

---

## Ozellikler

### Sohbet -- Tekil Hisse Analizi
- BIST-30 hisselerinden birini sec, Turkce soru sor
- Agent PDF, SQL ve haber kaynaklarini paralel tarar
- Sohbet hafizasi: konusmalar localStorage'da kalici, sidebar'da tarih grupli liste
  (Bugun / Dun / Bu Hafta / Daha Once), takip sorulari anlasilir
- Veri yoksa otomatik yfinance'den cekilir (auto-fetch)

### Karsilastirma -- Coklu Hisse
- 2 hisseyi yan yana kiyasla (metrik tablosu)
- F/K, PD/DD, net marj, ROE, ROA, FAVOK vb.
- Serbest soru-cevap (multi-ticker agent)

### Portfoy Dashboard
- Hisse ekleme/cikarma (Firestore'da kalici)
- Toplam deger, K/Z, agirlikli F/K, temettu verimi
- Sektor dagilimi (bar chart)
- Konsantrasyon uyarilari (>%30 hisse, >%40 sektor)
- Temettu takvimi (Turkce tarih)
- Portfoy haberleri + AI soru-cevap

### Guvenlik ve Kalite
- Firebase Auth (Google OAuth) + backend token dogrulama
- **Fail-safe auth:** `ENVIRONMENT` tanimli degilse production varsayilir — dev bypass kazara acilmaz
- **Text-to-SQL guard:** LLM'in urettigi sorgu SELECT-only + tek ifade; baglanti salt-okunur
- BIST-30 ticker whitelist — tum uclarda (`backend/constants.py` tek kaynak)
- **Rate limiting:** kullanici basina dakika + gun limiti (429 + Retry-After)
- **CORS:** `CORS_ORIGINS` ortam degiskeninden yonetilir
- Dosya yükleme: sadece PDF (magic byte kontrolu), max 50 MB, path traversal korumasi
- Tum endpoint'lerde timeout (agent 120s, fetch 60s)
- DB baglanti leak onleme (try/finally)
- Input validation + HTTPException
- `print()` --> `logging` migrasyonu (structured logging)
- 73 test (pytest): health, auth, validation, SQL guard, rate limit, dosya adi guvenligi
- CI/CD: GitHub Actions (her push/PR'da otomatik test + build)

---

## API Endpoint'leri

| Method | Endpoint | Aciklama |
|---|---|---|
| GET | `/api/health` | Saglik kontrolu |
| POST | `/api/upload/sync` | PDF yukle ve indexle |
| POST | `/api/ask` | Soru sor, agent yanitini al |
| POST | `/api/fetch-data` | yfinance verisini SQLite'a cek |
| POST | `/api/fetch-news` | Haber verilerini cek |
| GET | `/api/compare/metrics` | 2 ticker icin metrik karsilastirmasi |
| POST | `/api/compare/ask` | Karsilastirma sorusu sor |
| POST | `/api/portfolio/metrics` | Portfoy metrikleri, sektor dagilimi, uyarilar |
| POST | `/api/portfolio/ask` | Portfoy AI soru-cevap |
| POST | `/api/portfolio/news` | Portfoy hisselerine ait haberler |

---

## Kurulum

### Gereksinimler
- Python 3.12+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) paket yoneticisi
- Qdrant Cloud hesabi (ucretsiz tier yeterli)
- Anthropic API anahtari

### 1. Ortam Degiskenleri

```bash
cp .env.example .env
# .env dosyasini duzenle:
# ANTHROPIC_API_KEY, QDRANT_URL, QDRANT_API_KEY

cp frontend/.env.example frontend/.env
# Firebase config degerlerini ekle
```

### 2. Backend

```bash
uv sync
uv run uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### 4. Testler

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

---

## Proje Yapisi

```
agentick.io/
├── backend/
│   ├── main.py                   # FastAPI app + CORS (env) + logging + startup auth init
│   ├── auth.py                   # Firebase Auth (fail-safe: varsayilan production)
│   ├── constants.py              # BIST-30 whitelist + ticker dogrulama (tek kaynak)
│   ├── rate_limit.py             # Kullanici basina kayan pencere kotasi
│   ├── routes/
│   │   ├── query.py              # POST /api/ask (120s timeout)
│   │   ├── upload.py             # POST /api/upload (ticker whitelist, 50MB limit)
│   │   ├── fetch_data.py         # POST /api/fetch-data (60s timeout)
│   │   ├── fetch_news.py         # POST /api/fetch-news
│   │   ├── compare.py            # GET /api/compare/metrics, POST /api/compare/ask
│   │   └── portfolio.py          # POST /api/portfolio/metrics, ask, news
│   └── services/
│       ├── pdf_pipeline.py       # PDF --> SQLite + Qdrant
│       └── metrics_utils.py      # Paylasilan metrik helper'lar
├── src/
│   ├── agent/                    # LangGraph agent
│   │   ├── state.py              # AgentState (tickers alani dahil)
│   │   ├── planner_node.py       # Tek + coklu ticker prompt'lari
│   │   ├── router_node.py        # Auto-fetch + per-task ticker + timeout
│   │   ├── critic_node.py
│   │   ├── synthesizer_node.py   # Tek + karsilastirma prompt'lari
│   │   └── graph.py              # run_agent()
│   ├── retrievers/
│   │   ├── sql_retriever.py      # Text-to-SQL (SQLite, 8 tablo)
│   │   ├── vector_retriever.py   # Qdrant semantic search (singleton, thread-safe)
│   │   └── news_retriever.py     # Haber arama (AND keyword)
│   └── ingestion/
│       ├── bist_finance_client.py    # yfinance --> SQLite (temettu + bedelsiz + sektor)
│       ├── news_client.py            # RSS haber cekme
│       ├── pdf_chunker.py            # PDF --> text chunks
│       └── build_vector_index.py     # chunks --> Qdrant
├── frontend/
│   └── src/
│       ├── main.tsx              # BrowserRouter + AuthProvider
│       ├── App.tsx               # Auth guard + Layout + Routes
│       ├── config/firebase.ts    # Firebase config
│       ├── contexts/AuthContext.tsx
│       ├── constants/tickers.ts  # BIST-30 tek kaynak
│       ├── pages/
│       │   ├── LoginPage.tsx     # Landing page (9 bolum)
│       │   ├── ChatPage.tsx      # Sohbet sayfasi
│       │   ├── ComparePage.tsx   # Karsilastirma sayfasi
│       │   └── PortfolioPage.tsx # Portfoy dashboard
│       ├── components/           # 15+ UI bileseni
│       ├── api/client.ts
│       └── services/
│           ├── conversationStorage.ts
│           └── portfolioService.ts
├── tests/
│   ├── conftest.py               # Shared fixtures (TestClient + state reset)
│   ├── test_health.py            # Health endpoint testi
│   ├── test_auth.py              # Auth fail-safe testleri
│   ├── test_validation.py        # Input validation + ticker whitelist testleri
│   ├── test_sql_guard.py         # Text-to-SQL guvenlik testleri
│   ├── test_rate_limit.py        # Kota testleri
│   └── test_upload_security.py   # Dosya adi / path traversal testleri
├── .github/workflows/ci.yml     # CI/CD pipeline
├── data/
│   ├── raw/                      # Yuklenen PDF'ler
│   └── bist_financials.db        # SQLite
├── pyproject.toml
├── .env.example
└── frontend/.env.example
```

---

## Desteklenen Hisseler (BIST-30)

```
AKBNK  AKSEN  ARCLK  ASELS  BIMAS
EKGYO  ENKAI  EREGL  FROTO  GARAN
GUBRF  HALKB  ISCTR  KCHOL  KONTR
KOZAL  KRDMD  ODAS   PETKM  PGSUS
SAHOL  SASA   SISE   TAVHL  TCELL
THYAO  TOASO  TUPRS  VAKBN  YKBNK
```

---

## Lisans

Bu proje ozel kullanim icindir.
