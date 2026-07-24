# agentick.io — Sistem Mimarisi

> BIST hisseleri için Türkçe agentic RAG platformu.
> KAP faaliyet raporları + yfinance finansal verileri + LangGraph orchestration.

---

## 1. Genel Akış

```
Kullanıcı (browser)
    │  PDF yükle / soru sor / ticker seç / karşılaştır / portföy yönet
    ▼
React Frontend (Vite, port 5173, react-router-dom)
    │  POST /api/upload/sync
    │  POST /api/ask
    │  POST /api/fetch-data
    │  GET  /api/compare/metrics
    │  POST /api/compare/ask
    │  POST /api/portfolio/metrics
    │  POST /api/portfolio/ask
    │  POST /api/portfolio/news
    ▼
FastAPI Backend (Uvicorn, port 8000)
    │
    ├── PDF Pipeline ──────────────────────────────────────┐
    │   pdfplumber → pdf_tables (SQLite)                   │
    │   PyMuPDF + pdf_chunker → embedding → Qdrant         │
    │   yfinance → income_statement / balance_sheet / ...  │
    │                                                       ▼
    └── LangGraph Agent                              SQLite + Qdrant
            │
            ▼
        PLANNER NODE (Claude Haiku)
            Sohbet geçmişini okur
            Soruyu standalone hale getirir
            Alt görevler üretir: [{query, type, ticker?}]
            Çoklu ticker → PLANNER_PROMPT_MULTI (her ticker için ayrı sub_task)
            │
            ▼
        ROUTER NODE (asyncio.gather + 30s timeout/task)
            ├── type="sql"    → SQL Retriever → SQLite (per-task ticker)
            │                    └── boş dönerse → auto-fetch (yfinance) → tekrar sorgula
            ├── type="vector" → Vector Retriever → Qdrant (15s timeout)
            └── type="news"   → News Retriever → SQLite (news_articles)
            │
            ▼
        CRITIC NODE (Claude Haiku)
            "Bilgi yeterli mi?"
            ├── SUFFICIENT  → SYNTHESIZER'a geç
            └── INSUFFICIENT → PLANNER'a geri dön (max 3 tur)
            │
            ▼
        SYNTHESIZER NODE (Claude Sonnet 4.6)
            Max 12 kaynak (skora göre sıralı)
            Türkçe, kaynaklı cevap
            Çoklu ticker → SYSTEM_PROMPT_COMPARE (karşılaştırmalı analiz)
            "Bu bilgi yatırım tavsiyesi değildir."
            │
            ▼
        JSON yanıt → Frontend
```

---

## 2. LangGraph Agent

### AgentState

```python
class AgentState(TypedDict):
    question: str                              # Kullanıcının orijinal sorusu
    ticker: str                                # Hisse kodu (ör. THYAO)
    tickers: list[str]                         # Çoklu karşılaştırma için ticker listesi
    conversation_history: list[dict]           # Önceki mesajlar (son 6)
    standalone_question: str                   # Planner'ın rewrite ettiği soru
    sub_tasks: list[dict]                      # [{"query": "...", "type": "sql"|"vector", "ticker"?: "..."}]
    retrieved: Annotated[list[dict], operator.add]  # Birikimli retriever sonuçları
    critic_feedback: str                       # "SUFFICIENT" veya "INSUFFICIENT: ..."
    retry_count: int                           # Kaç kez retry yapıldı (max 3)
    final_answer: str                          # Synthesizer çıktısı
```

### Graf Yapısı

```
START
  ↓
planner_node
  ↓
router_node
  ↓
critic_node ──── "retry" ──→ planner_node
  │
  └── "synthesize" ──→ synthesizer_node ──→ END
```

### Node Detayları

| Node | Model | Görev |
|---|---|---|
| Planner | Claude Haiku 4.5 | Soruyu rewrite et, sub_task üret. Çoklu ticker → her ticker için ayrı sub_task (ticker alanı dahil) |
| Router | — | asyncio.gather + 30s timeout/task, per-task ticker desteği, duplicate filtreleme, auto-fetch |
| Critic | Claude Haiku 4.5 | Toplanan bilginin yeterliliğini değerlendir |
| Synthesizer | Claude Sonnet 4.6 | Max 12 kaynak, Türkçe, kaynaklı yanıt. Çoklu ticker → karşılaştırmalı analiz prompt'u |

---

## 3. Retriever Katmanı

### SQL Retriever (`src/retrievers/sql_retriever.py`)

**Akış:**
1. Claude Haiku → Türkçe soru → SQL sorgusu
2. SQLite'ta çalıştır
3. Sonuçları düz metin + citation olarak döndür

**Desteklenen tablolar:**

| Tablo | İçerik | Kaynak |
|---|---|---|
| `income_statement` | Gelir, brüt kâr, EBITDA, net kâr | yfinance |
| `balance_sheet` | Varlıklar, borç, özkaynak, nakit | yfinance |
| `cash_flow` | Operasyonel, yatırım, finansman, serbest nakit akışı | yfinance |
| `ratios` | P/E, P/B, net marj, ROE, ROA, D/E, piyasa değeri, fiyat, sektör | yfinance |
| `dividends` | Temettü tarihi ve hisse başı tutar | yfinance |
| `stock_splits` | Bedelsiz sermaye artırımı / hisse bölünme tarihi ve oranı | yfinance |
| `pdf_tables` | PDF'den çıkarılan tablolar (pipe-delimited metin) | pdfplumber |
| `news_articles` | Haber başlıkları, özetleri, kaynak ve tarih | RSS (Bloomberg HT vb.) |

**Citation formatları:**
- yfinance tabloları: `yfinance — THYAO income_statement (2024-12-31 – 2022-12-31)`
- PDF tabloları: `PDF — THYAO THYAO_faaliyet_2026.pdf`

**Önemli davranışlar:**
- `pdf_tables` sorgularında OR koşulları parantez içinde (prompt kuralı)
- `pdf_tables` çıktısı: `[Sayfa N — dosya_adı]\n{table_text}` formatı
- Finansal tablo çıktısı: `period_date=... | net_margin=...` formatı
- Temettü verimi sorulursa: `dividends` + `ratios.current_price` JOIN ile hesaplanır

### Auto-Fetch Mekanizması

Router'da SQL retriever boş sonuç döndüğünde:
1. `fetch_and_store(ticker)` çağrılır (yfinance'den tüm veri çekilir)
2. Aynı SQL sorgusu tekrar çalıştırılır
3. Veri zaten varsa fetch tetiklenmez (ilk sorgu sonuç döner)

```python
# router_node.py — run_task() içinde
task_ticker = task.get("ticker", state["ticker"])  # per-task ticker desteği
if task_type == "sql":
    results = await asyncio.to_thread(sql_search, query, task_ticker)
    if not results:
        from src.ingestion.bist_finance_client import fetch_and_store
        await asyncio.to_thread(fetch_and_store, task_ticker)
        results = await asyncio.to_thread(sql_search, query, task_ticker)
    return results

# Her task 30s timeout ile sarılır — takılırsa atlanır
async def run_task_with_timeout(task):
    return await asyncio.wait_for(run_task(task), timeout=30)
```

### Vector Retriever (`src/retrievers/vector_retriever.py`)

**Model:** `paraphrase-multilingual-mpnet-base-v2` (768 boyut, Türkçe destekli)
**Collection:** `kap_filings`
**Filtreleme:** `ticker` payload filtresi ile hisseye özgü arama

**Citation formatı:** `KAP — THYAO Faaliyet Raporu, s.23 (Finansal Durum)`

**Çıktı yapısı:**
```python
{
    "text": "chunk metni",
    "ticker": "THYAO",
    "page": 23,
    "section": "Finansal Durum",
    "source_file": "THYAO_faaliyet_2026.pdf",
    "score": 0.87,           # cosine similarity
    "citation": "KAP — ..."
}
```

### News Retriever (`src/retrievers/news_retriever.py`)

**Kaynak:** RSS beslemeleri (Bloomberg HT, Dünya gazetesi vb.)
**Depolama:** SQLite `news_articles` tablosu
**Süre:** 30 günlük cache, stale olunca otomatik yenileme

**Skor hesaplama:**
- 0.5 baz puan
- +0.3 başlıkta keyword eşleşmesi
- +0.1 özette keyword eşleşmesi
- +0.1 ticker eşleşmesi
- +0.1 yayın tarihi varsa

**Citation formatı:** `Haber — Bloomberg HT (2026-07-20)`

### Router'da Duplicate Önleme

Her retry'da `state["retrieved"]` içindeki mevcut `text` değerleri bir `set`'e alınır. Yeni sonuçlar bu set'e göre filtrelenir — aynı chunk iki kez eklenmez. Her retry gerçekten yeni bilgi ekler.

---

## 4. Ingestion Pipeline

### PDF Yükleme Akışı

```
POST /api/upload/sync
    ↓
backend/services/pdf_pipeline.py → process_pdf(pdf_path, ticker)
    │
    ├── 1. Tablo Çıkarma (pdfplumber)
    │       Her sayfadaki tabloları al
    │       Satırları "| " ile birleştir
    │       SQLite pdf_tables'a yaz
    │       (Aynı dosya yeniden yüklenirse önce eski kayıtları sil)
    │
    ├── 2. Metin Indexleme
    │       PyMuPDF → sayfa bazlı metin
    │       pdf_chunker → semantic chunks (600 token, 80 overlap)
    │       SentenceTransformer → 768D embedding
    │       Qdrant → upsert (ticker payload filtresi)
    │
    └── 3. yfinance Güncellemesi
            bist_finance_client.fetch_and_store(ticker)
            income_statement, balance_sheet, cash_flow, ratios → SQLite
```

### yfinance Çekme Akışı

```
POST /api/fetch-data {ticker: "THYAO"}
    ↓
bist_finance_client.fetch_and_store("THYAO")
    ↓
yf.Ticker("THYAO.IS")
    ├── income_stmt → income_statement tablosu
    ├── balance_sheet → balance_sheet tablosu
    ├── cashflow → cash_flow tablosu
    ├── info (P/E, P/B, ROE, fiyat, sektör...) → ratios tablosu (sector kolonu dahil)
    ├── dividends → dividends tablosu
    └── splits → stock_splits tablosu (bedelsiz sermaye artırımı)
```

---

## 5. FastAPI Backend

### Endpoint'ler

| Method | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/health` | Sağlık kontrolü, versiyon |
| POST | `/api/upload` | PDF yükle (arka planda, async) |
| POST | `/api/upload/sync` | PDF yükle ve indexle (senkron, frontend kullanır) |
| POST | `/api/ask` | Soru sor, LangGraph agent yanıtını bekle |
| POST | `/api/fetch-data` | yfinance verisini çek ve SQLite'a yaz |
| GET | `/api/compare/metrics` | 2 ticker için metrik karşılaştırması (her çağrıda yfinance auto-fetch) |
| POST | `/api/compare/ask` | Karşılaştırma chat sorusu (multi-ticker agent) |
| POST | `/api/portfolio/metrics` | Portföy metrikleri: per-holding K/Z, sektör dağılımı, uyarılar, temettü takvimi |
| POST | `/api/portfolio/ask` | Portföy AI soru-cevap (multi-ticker agent) |
| POST | `/api/portfolio/news` | Portföy hisselerine ait haberler (ticker tag + keyword AND arama) |

### `/api/ask` Request / Response

```python
# Request
class AskRequest(BaseModel):
    question: str
    ticker: str
    conversation_history: list[dict] = []   # [{"role": "user|assistant", "content": "..."}]

# Response
{
    "answer": str,                           # Türkçe yanıt
    "ticker": str,
    "sub_tasks": list[dict],                 # [{"query": "...", "type": "sql|vector"}]
    "retrieved_count": int,                  # Toplam unique kaynak sayısı
    "retry_count": int,                      # Kaç retry yapıldı
    "critic_feedback": str                   # Son critic kararı
}
```

### `/api/compare/metrics` Request / Response

```python
# Request: GET /api/compare/metrics?tickers=THYAO,TUPRS

# Response
{
    "tickers": ["THYAO", "TUPRS"],
    "metrics": {
        "THYAO": {
            "current_price": 329.50,
            "market_cap": 454000000000,
            "pe_ratio": 8.5,
            "pb_ratio": 1.2,
            "net_margin": 12.08,
            "roe": 0.35,
            "roa": 0.08,
            "debt_to_equity": 2.1,
            "dividend_yield": 2.57,
            "revenue": 250000000000,
            "net_income": 30000000000,
            "ebitda": 55000000000,
            ...
        },
        "TUPRS": { ... }
    }
}
```

### `/api/compare/ask` Request / Response

```python
# Request
class CompareAskRequest(BaseModel):
    question: str
    tickers: list[str]                        # ["GARAN", "AKBNK"]
    conversation_history: list[dict] = []

# Response
{
    "answer": str,                           # Karşılaştırmalı Türkçe yanıt
    "tickers": list[str],
    "sub_tasks": list[dict],                 # [{"query": "...", "type": "sql", "ticker": "GARAN"}, ...]
    "retrieved_count": int,
    "retry_count": int,
    "critic_feedback": str
}
```

### `/api/portfolio/metrics` Request / Response

```python
# Request
class PortfolioMetricsRequest(BaseModel):
    holdings: list[HoldingInput]  # [{"ticker": "THYAO", "shares": 100, "avgCost": 250.0}]

# Response
{
    "holdings": [
        {
            "ticker": "THYAO",
            "shares": 100,
            "avgCost": 250.0,
            "currentPrice": 329.50,
            "marketValue": 32950.0,
            "costBasis": 25000.0,
            "profitLoss": 7950.0,
            "profitLossPct": 31.8,
            "weight": 65.2,
            "sector": "Industrials",
            "pe_ratio": 8.5,
            "dividend_yield": 2.57,
            "net_margin": 12.08
        }
    ],
    "summary": {
        "totalValue": 50500.0,
        "totalCost": 38000.0,
        "totalProfitLoss": 12500.0,
        "totalProfitLossPct": 32.89,
        "weightedPE": 9.2,
        "weightedDividendYield": 2.1,
        "weightedNetMargin": 10.5
    },
    "sectorAllocation": [
        {"sector": "Industrials", "weight": 65.2, "tickers": ["THYAO"]}
    ],
    "warnings": ["THYAO portföyün %65.2'ini oluşturuyor (>%30)"],
    "dividends": [
        {"ticker": "THYAO", "ex_date": "2025-09-02", "amount": 1.50}
    ]
}
```

### `/api/portfolio/ask` — `/api/compare/ask` ile aynı format

### `/api/portfolio/news` Request / Response

```python
# Request
class PortfolioNewsRequest(BaseModel):
    tickers: list[str]  # ["THYAO", "TUPRS"]

# Response
{
    "tickers": ["THYAO", "TUPRS"],
    "count": 8,
    "articles": [
        {
            "source": "Bloomberg HT",
            "title": "THY yolcu sayısı rekoru...",
            "link": "https://...",
            "summary": "...",
            "published_at": "2026-07-24 10:30:00",
            "tickers": "THYAO,TAVHL",
            "ticker": "THYAO"
        }
    ]
}
```

---

## 6. React Frontend

### Bileşen Hiyerarşisi

```
main.tsx (BrowserRouter + AuthProvider)
└── App.tsx (Auth guard + Layout shell + Routes)
    │
    ├── [!user] → LoginPage.tsx (Landing page — 9 bölüm)
    │   ├── Navbar (frosted glass, logo + "Giriş Yap" + "Ücretsiz Başla")
    │   ├── Hero Section (min-h-screen, 2 sütun, inline SVG chat mockup)
    │   ├── Trust Strip (4 metrik: 500+ Hisse, RAG Motoru, Gerçek Zamanlı, Türkçe AI)
    │   ├── Nasıl Çalışır? (3 adım, dashed connector, numaralı ikonlar)
    │   ├── Özellikler (6 renkli kart, lg:grid-cols-3)
    │   ├── Platform Önizleme (2 sütun, browser frame SVG mockup)
    │   ├── FAQ Accordion (5 soru, useState toggle, chevron animasyonu)
    │   ├── Final CTA (bg-gray-900, beyaz text + CTA)
    │   └── Footer (3 sütun: logo+açıklama | ürün linkleri | iletişim, © 2026)
    │
    └── [user] → Layout shell (Sidebar + Routes)
        ├── Sidebar.tsx                 # Sohbet/Karşılaştır/Portföy navigasyonu + konuşma listesi
        │   ├── [Navigasyon tabları]    # useNavigate + useLocation
        │   └── [Conversation listesi]
        └── Ana Alan (Routes)
            ├── Route "/" → ChatPage.tsx
            │   ├── Header (chat modunda)   # Logo + ticker dropdown
            │   ├── [Boş durum]             # Logo + öneri sorular + ChatInput
            │   └── [Chat durumu]
            │       ├── Message.tsx (×N)
            │       ├── ThinkingIndicator
            │       └── ChatInput.tsx
            ├── Route "/compare" → ComparePage.tsx
            │   ├── Header              # Logo + "Karşılaştırma" etiketi
            │   ├── TickerSelector.tsx   # Multi-select (2 ticker, badge + dropdown)
            │   ├── ComparisonTable.tsx  # Metrik tablosu (12 satır × N kolon)
            │   └── ComparisonChat.tsx   # Karşılaştırma Q&A (ephemeral)
            │       ├── Message.tsx (×N)
            │       ├── ThinkingIndicator
            │       └── Input bar (ticker badge'leri + textarea + send)
            └── Route "/portfolio" → PortfolioPage.tsx
                ├── PortfolioManager.tsx        # Holding CRUD (ticker dropdown + lot + maliyet)
                ├── PortfolioSummaryCards.tsx   # 6 kart (Değer, Maliyet, K/Z, K/Z%, F/K, Temettü)
                ├── ConcentrationWarnings.tsx   # Amber uyarı kartları (>%30 hisse, >%40 sektör)
                ├── SectorChart.tsx            # CSS bar chart (8 renk paleti)
                ├── DividendCalendar.tsx        # Temettü takvimi (Türkçe tarih formatı)
                ├── PortfolioHoldingsTable.tsx  # 9 kolon detay tablosu
                ├── PortfolioNews.tsx           # Portföy hisselerine ait haberler
                └── PortfolioChat.tsx           # Portföy AI soru-cevap
                    ├── Message.tsx (×N)
                    ├── ThinkingIndicator
                    └── Input bar (ticker badge'leri + textarea + send)
```

### Auth Akışı

```
Kullanıcı ilk gelir → App.tsx: user=null → LoginPage gösterilir
    │
    ├── "Ücretsiz Başla" / "Giriş Yap" tıklanır
    │       ↓
    │   signInWithGoogle() → signInWithPopup(auth, googleProvider)
    │       ↓
    │   Firebase popup açılır → Google hesabı seçilir
    │       ↓
    │   onAuthStateChanged → user set edilir → App.tsx re-render
    │       ↓
    │   user !== null → Layout shell + Routes gösterilir
    │
    └── Sidebar'da "Çıkış" tıklanır
            ↓
        signOut() → firebaseSignOut(auth)
            ↓
        user = null → LoginPage'e geri dönülür
```

### State Yönetimi (App.tsx)

```typescript
// Auth (AuthContext üzerinden)
user: User | null               // Firebase Auth user nesnesi
loading: boolean                // Auth durumu yükleniyor mu

// App state
messages: MessageData[]         // Aktif konuşma mesajları
ticker: string                  // Seçili hisse kodu
loading: boolean                // Agent yanıt bekliyor
suggestion: string | undefined  // Öneri soru chip'i tıklandığında
```

### Shared Constants

```typescript
// frontend/src/constants/tickers.ts — tek kaynak
export const BIST_TICKERS = ['AKBNK', 'AKSEN', ...] as const
export type BistTicker = typeof BIST_TICKERS[number]
// App.tsx, ChatInput.tsx ve TickerSelector.tsx bu dosyadan import eder
```

### Konuşma Hafızası

- Her konuşma localStorage'da ayrı bir `Conversation` nesnesi olarak saklanır.
- `handleSend()` her mesaj sonrası localStorage'ı günceller.
- `/api/ask` çağrısında `conversation_history` olarak son N mesaj gönderilir.
- Planner bu geçmişi kullanarak takip sorularını standalone hale getirir.

### ChatInput Özellikleri

- **Ticker dropdown:** 30 BIST hissesi (alfabetik)
- **PDF upload:** `POST /api/upload/sync`, anlık progress bar
- **Fetch data butonu (↺):** `POST /api/fetch-data`, spinner + başarı/hata mesajı
- **Textarea:** Enter = gönder, Shift+Enter = satır sonu, auto-resize

### conversationStorage.ts

```typescript
interface Conversation {
    id: string
    title: string               // İlk sorudan otomatik üretilir
    ticker: string
    messages: MessageData[]
    createdAt: string
    updatedAt: string
}
```

Gruplar: Bugün / Dün / Bu Hafta / Daha Önce

---

## 7. Veri Modelleri

### SQLite — `data/bist_financials.db`

```sql
CREATE TABLE income_statement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    period_date TEXT,           -- YYYY-MM-DD
    revenue REAL,               -- TL
    gross_profit REAL,
    ebitda REAL,
    net_income REAL
);

CREATE TABLE balance_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    period_date TEXT,
    total_assets REAL,
    total_debt REAL,
    total_equity REAL,
    cash REAL
);

CREATE TABLE cash_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    period_date TEXT,
    operating_cf REAL,
    investing_cf REAL,
    financing_cf REAL,
    free_cf REAL
);

CREATE TABLE ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    period_date TEXT,
    pe_ratio REAL,
    pb_ratio REAL,
    net_margin REAL,            -- %
    roe REAL,
    roa REAL,
    debt_to_equity REAL,
    market_cap REAL,
    current_price REAL,         -- TRY
    sector TEXT                 -- Sektör (yfinance info.sector)
);

CREATE TABLE dividends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    ex_date TEXT,               -- Temettü ödeme tarihi (YYYY-MM-DD)
    amount REAL                 -- Hisse başı temettü tutarı (TL)
);

CREATE TABLE stock_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    split_date TEXT,            -- Bölünme tarihi (YYYY-MM-DD)
    ratio REAL                  -- Bölünme oranı (ör. 2.0 = %100 bedelsiz)
);

CREATE TABLE pdf_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    source_file TEXT NOT NULL,
    page INTEGER,
    table_index INTEGER,        -- Sayfadaki sıra (0'dan başlar)
    table_text TEXT NOT NULL,   -- "Sütun1 | Sütun2\nSatır1 | Satır2"
    uploaded_at TEXT
);

CREATE TABLE news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,                -- Haber kaynağı (ör. Bloomberg HT)
    title TEXT,
    link TEXT UNIQUE,
    summary TEXT,
    published_at TEXT,
    fetched_at TEXT,
    tickers TEXT                -- Virgülle ayrılmış ticker'lar (ör. "THYAO,TAVHL")
);
```

### Qdrant — `kap_filings` Collection

```
Vector: 768 boyut, cosine distance
Payload:
    ticker: keyword
    page: integer
    section: keyword
    source_file: keyword
    chunk_index: integer
```

---

## 8. Teknoloji Stack

| Katman | Teknoloji | Versiyon |
|---|---|---|
| LLM (Sentez) | Claude Sonnet 4.6 | claude-sonnet-4-6 |
| LLM (Planner/Critic) | Claude Haiku 4.5 | claude-haiku-4-5-20251001 |
| Agent Orkestrasyonu | LangGraph | ≥0.2.0 |
| Embedding (lokal) | paraphrase-multilingual-mpnet-base-v2 | sentence-transformers ≥5.6 |
| Vektör DB | Qdrant Cloud | EU-Central-1 |
| İlişkisel DB | SQLite | Python built-in |
| Finansal Veri | yfinance | ≥1.5.1 |
| PDF — Metin | PyMuPDF (fitz) | ≥1.28.0 |
| PDF — Tablo | pdfplumber | ≥0.11.0 |
| Backend | FastAPI + Uvicorn | ≥0.115.0 |
| Frontend | React 18 + TypeScript | 18.3.1 + 5.5.3 |
| Auth | Firebase Authentication | Google OAuth popup |
| Routing | react-router-dom | ^7.x |
| Build | Vite | 5.4.8 |
| CSS | Tailwind CSS | 3.4.13 |
| İkonlar | lucide-react | latest |
| Gözlemlenebilirlik | LangSmith | LANGCHAIN_TRACING_V2=true |
| Paket Yönetimi (PY) | uv | latest |
| Paket Yönetimi (JS) | npm | latest |

---

## 9. Ortam Değişkenleri

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-...

# Vektör DB
QDRANT_URL=https://xxx.eu-central-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=...

# Firebase (frontend .env)
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...

# LangSmith (isteğe bağlı)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=agentick
```

---

## 10. Desteklenen BIST-30 Hisseleri

```
AKBNK  AKSEN  ARCLK  ASELS  BIMAS
EKGYO  ENKAI  EREGL  FROTO  GARAN
GUBRF  HALKB  ISCTR  KCHOL  KONTR
KOZAL  KRDMD  ODAS   PETKM  PGSUS
SAHOL  SASA   SISE   TAVHL  TCELL
THYAO  TOASO  TUPRS  VAKBN  YKBNK
```

---

## 11. İmplementasyon Durumu

| Bileşen | Durum |
|---|---|
| LangGraph agent (Planner → Router → Critic → Synthesizer) | ✅ |
| SQL Retriever (yfinance + pdf_tables) | ✅ |
| Vector Retriever (Qdrant) | ✅ |
| News Retriever (RSS haber arama) | ✅ |
| Temettü verisi (yfinance .dividends) | ✅ |
| Temettü verimi hesaplama (dividends JOIN ratios) | ✅ |
| Auto-fetch (SQL boş → yfinance'den çek → tekrar sorgula) | ✅ |
| PDF Pipeline (tablo + metin + yfinance) | ✅ |
| FastAPI backend (upload, ask, fetch-data, fetch-news) | ✅ |
| React frontend (sidebar, chat, ChatInput) | ✅ |
| Konuşma hafızası (localStorage + API) | ✅ |
| LangSmith tracing | ✅ |
| Router duplicate önleme | ✅ |
| BIST-30 ticker desteği | ✅ |
| Çoklu şirket karşılaştırma (2 ticker, metrik tablo + chat) | ✅ |
| React Router (/, /compare) | ✅ |
| Sidebar navigasyonu (Sohbet/Karşılaştır) | ✅ |
| Shared constants (BIST_TICKERS tek kaynak) | ✅ |
| Router task timeout (30s) + Qdrant timeout (15s) | ✅ |
| Firebase Auth (Google OAuth, AuthContext) | ✅ |
| Landing Page (9 bölüm, inline SVG mockup'lar, FAQ accordion) | ✅ |
| Auth guard (App.tsx'te user kontrolü) | ✅ |
| Portföy dashboard (Firestore CRUD, 8 bileşen, 3 endpoint) | ✅ |
| Sektör verisi (yfinance → ratios.sector) | ✅ |
| Bedelsiz sermaye artırımı (stock_splits tablosu) | ✅ |
| Haber AND keyword araması (false positive önleme) | ✅ |
| Paylaşılan metrik helper'lar (metrics_utils.py) | ✅ |
| Otomatik screening/alert | ❌ Planlandı |
| Kullanıcı kotası (Firestore) | ❌ Planlandı |
| Deployment (Railway / Vercel) | ❌ Planlandı |

---

## 12. Sonraki Adımlar

1. **Otomatik Screening/Alert** — Kriter bazlı hisse taraması, bildirim
2. **Zaman Serisi Takibi** — Watchlist, temettü/fiyat bildirimi
3. **KAP Entegrasyonu** — Özel durum açıklamaları, endeks değişiklikleri
4. **Deployment** — Railway (backend) + Vercel (frontend)
5. **Kullanıcı Kotası** — Firestore ile aylık sorgu limiti
6. **Eval sistemi** — 30 BIST sorusu ile doğruluk metrikleri
7. **Stripe Entegrasyonu** — ₺199/ay Pro abonelik
