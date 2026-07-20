# agentick.io

**BIST hisseleri için Türkçe AI finansal analist.**

Türk bireysel yatırımcıların KAP faaliyet raporları ve finansal tablolar üzerinden Türkçe sorular sorabildiği, kaynaklı cevaplar aldığı agentic RAG platformu.

---

## Nasıl Çalışır

Kullanıcı PDF yükler (KAP faaliyet raporu), ticker seçer ve Türkçe soru sorar. LangGraph agent PDF'teki tabloları ve metni, yfinance finansal verilerini ve haberleri paralel tarar; eksikse otomatik çeker; Türkçe ve kaynaklı cevap üretir.

```
Kullanıcı sorusu
      │
      ▼
  PLANNER   → soruyu alt görevlere böler (sql / vector / news)
      │
      ▼
  ROUTER    → paralel retriever çağrısı (asyncio.gather)
      │
      ├── SQL Retriever    (yfinance + PDF tabloları — SQLite)
      │                     └── boş dönerse → auto-fetch → tekrar sorgula
      ├── Vector Retriever (KAP rapor metni — Qdrant)
      └── News Retriever   (RSS haberler — SQLite)
      │
      ▼
  CRITIC    → bilgi yeterli mi? değilse PLANNER'a geri dön (max 3 tur)
      │
      ▼
  SYNTHESIZER → Türkçe, kaynaklı cevap (Claude Sonnet 4.6)
```

---

## Teknoloji Stack

| Katman | Teknoloji |
|---|---|
| LLM (Sentez) | Claude Sonnet 4.6 |
| LLM (Planner/Critic) | Claude Haiku 4.5 |
| Agent Orkestrasyonu | LangGraph |
| Embedding | paraphrase-multilingual-mpnet-base-v2 (lokal) |
| Vektör DB | Qdrant Cloud |
| İlişkisel DB | SQLite (`data/bist_financials.db`) |
| Finansal Veri | yfinance |
| PDF İşleme | pdfplumber (tablolar) + PyMuPDF (metin) |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Gözlemlenebilirlik | LangSmith |

---

## Kurulum

### Gereksinimler
- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) paket yöneticisi
- Qdrant Cloud hesabı (ücretsiz tier yeterli)
- Anthropic API anahtarı

### 1. Ortam Değişkenleri

```bash
cp .env.example .env
# .env dosyasını düzenle:
# ANTHROPIC_API_KEY, QDRANT_URL, QDRANT_API_KEY
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

---

## Kullanım

1. **PDF Yükle** — Siteye gir, ticker seç (ör. THYAO), KAP'tan indirdiğin PDF'i yükle.
2. **Veri Güncelle** — `↺` butonuna tıkla, yfinance'den güncel finansal veriler çekilir (veya veri yoksa otomatik çekilir).
3. **Soru Sor** — Örnekler:
   - "2024 net marjı nedir?" (SQL retriever)
   - "Yönetimin büyüme stratejisi nedir?" (Vector retriever)
   - "Son temettü tutarı ve verimi ne?" (SQL — dividends + ratios JOIN)
   - "Risk faktörleri nelerdir?" (Vector — PDF'den)
   - "Son haberler neler?" (News retriever)
4. **Kaynaklı Cevap** — Her iddia kaynak göstererek yanıtlanır.

---

## API Endpoint'leri

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/upload/sync` | PDF yükle ve indexle (senkron) |
| POST | `/api/fetch-data` | yfinance verisini SQLite'a çek |
| POST | `/api/fetch-news` | Haber verilerini çek |
| POST | `/api/ask` | Soru sor, agent yanıtını al |
| GET | `/api/health` | Sağlık kontrolü |

### `/api/ask` Örnek İstek

```json
{
  "question": "THYAO'nun 2024 net kâr marjı nedir?",
  "ticker": "THYAO",
  "conversation_history": []
}
```

### `/api/ask` Örnek Yanıt

```json
{
  "answer": "THYAO'nun 2024 net kâr marjı %15,1'dir... (Kaynak: yfinance — THYAO ratios)\n\nBu bilgi yatırım tavsiyesi değildir.",
  "ticker": "THYAO",
  "sub_tasks": [{"query": "THYAO 2024 net marj", "type": "sql"}],
  "retrieved_count": 4,
  "retry_count": 1,
  "critic_feedback": "SUFFICIENT"
}
```

---

## Desteklenen Hisseler (BIST-30)

`AKBNK AKSEN ARCLK ASELS BIMAS EKGYO ENKAI EREGL FROTO GARAN`
`GUBRF HALKB ISCTR KCHOL KONTR KOZAL KRDMD ODAS PETKM PGSUS`
`SAHOL SASA SISE TAVHL TCELL THYAO TOASO TUPRS VAKBN YKBNK`

---

## Proje Yapısı

```
agentick.io/
├── backend/                  # FastAPI
│   ├── main.py
│   ├── routes/
│   │   ├── upload.py         # POST /api/upload
│   │   ├── query.py          # POST /api/ask
│   │   └── fetch_data.py     # POST /api/fetch-data
│   └── services/
│       └── pdf_pipeline.py   # PDF → SQLite + Qdrant
├── src/
│   ├── agent/                # LangGraph agent
│   │   ├── state.py
│   │   ├── planner_node.py
│   │   ├── router_node.py
│   │   ├── critic_node.py
│   │   ├── synthesizer_node.py
│   │   └── graph.py
│   ├── retrievers/
│   │   ├── sql_retriever.py    # Text-to-SQL (SQLite)
│   │   ├── vector_retriever.py # Qdrant semantic search
│   │   └── news_retriever.py   # Haber arama
│   └── ingestion/
│       ├── bist_finance_client.py  # yfinance → SQLite (temettü dahil)
│       ├── news_client.py          # RSS haber çekme
│       ├── pdf_chunker.py          # PDF → text chunks
│       └── build_vector_index.py   # chunks → Qdrant
├── frontend/                 # React + Vite
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── AgentLogo.tsx
│       │   ├── ChatInput.tsx
│       │   ├── Message.tsx
│       │   ├── Sidebar.tsx
│       │   └── ThinkingIndicator.tsx
│       ├── api/client.ts
│       └── services/conversationStorage.ts
├── data/
│   ├── raw/                  # Yüklenen PDF'ler
│   └── bist_financials.db    # SQLite
├── pyproject.toml
└── .env.example
```
