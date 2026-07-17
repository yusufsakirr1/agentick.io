# agentick.io

**BIST hisseleri için Türkçe AI finansal analist.**

Türk bireysel yatırımcıların KAP faaliyet raporları, finansal tablolar ve güncel haberler üzerinden Türkçe sorular sorabildiği, kaynaklı cevaplar aldığı agentic RAG platformu.

> Bloomberg ve Perplexity bu nişi karşılamıyor. KAP verileri + Türkçe + agentic reasoning.

---

## Nasıl Çalışır

Kullanıcı bir hisse kodu ve Türkçe soru girer. Agent dört veri kaynağını paralel tarar, eksik bilgiyi fark edip ek arama yapar, tüm bulguları Türkçe ve kaynaklı tek cevaba dönüştürür.

```
Soru
 │
 ▼
PLANNER   → soruyu alt görevlere böler, kaynak tipini sınıflandırır
 │
 ▼
ROUTER    → paralel retriever çağrısı (asyncio.gather)
 │
 ├── SQL Retriever      (yfinance — fiyat, bilanço, oranlar)
 ├── Vector RAG         (KAP faaliyet raporları — Qdrant)
 ├── Haber Retriever    (Bloomberg HT, Dünya, Reuters TR)
 └── KAP Özel Durum     (temettü, sermaye artırımı, YK kararları)
 │
 ▼
CRITIC    → bilgi yeterli mi? değilse Router'a geri dön (max 3 tur)
 │
 ▼
SYNTHESIZER → Türkçe, kaynak gösterimli nihai cevap + KAP linkleri
```

---

## Stack

| Katman | Teknoloji |
|---|---|
| Agent orkestrasyonu | LangGraph |
| LLM | Claude Sonnet (Anthropic) |
| Embedding | paraphrase-multilingual-mpnet-base-v2 (lokal) → voyage-3 (prod) |
| Vector DB | Qdrant Cloud |
| Finansal veri | yfinance (`.IS` suffix) |
| İlişkisel DB | SQLite → Supabase PostgreSQL |
| Backend | FastAPI |
| Frontend | Next.js + shadcn/ui |
| Auth | Supabase Auth |
| Ödeme | Stripe |
| Gözlemlenebilirlik | Langfuse |
| Deployment | Railway |
| Ortam | uv |

---

## İş Modeli

**Freemium SaaS** — Ayda 5 sorgu ücretsiz, sonrası aylık abonelik.

---

## Durum

| Faz | İçerik | Durum |
|---|---|---|
| 1 | KAP veri katmanı + naive RAG | ✅ Tamamlandı |
| 2 | 4 retriever bağımsız çalışır | 🔄 Devam ediyor |
| 3 | LangGraph agent orkestrasyonu | Bekliyor |
| 4 | Self-critique / retry döngüsü | Bekliyor |
| 5 | Synthesizer + kaynak gösterme | Bekliyor |
| 6 | Auth + Freemium + Stripe | Bekliyor |
| 7 | Next.js frontend | Bekliyor |
| 8 | Eval sistemi | Bekliyor |
| 9 | Lansman | Bekliyor |

---

## Kurulum

```bash
git clone https://github.com/yusufsakirr1/agentick.io
cd agentick.io
uv sync
cp .env.example .env  # API keylerini doldur
```

```bash
# Vektör indeksini oluştur (önce data/raw/ altına KAP PDF'i koy)
uv run python src/ingestion/build_vector_index.py

# CLI testi
uv run python src/cli_test.py
```

---

## Ortam Değişkenleri

`.env.example` dosyasını kopyalayıp doldurun:

```
ANTHROPIC_API_KEY=
VOYAGE_API_KEY=
QDRANT_URL=
QDRANT_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
MAX_RETRY_COUNT=3
KAP_REQUEST_DELAY_SECONDS=2
```

---

## Klasör Yapısı

```
agentick.io/
├── data/
│   └── raw/                    ← KAP'tan indirilen PDF'ler
└── src/
    ├── ingestion/
    │   ├── kap_client.py       ← KAP PDF indirme
    │   ├── pdf_chunker.py      ← Türkçe PDF → chunk
    │   └── build_vector_index.py
    ├── retrievers/
    │   ├── vector_retriever.py ← Qdrant semantic search
    │   ├── sql_retriever.py    ← text-to-SQL (yfinance)
    │   ├── news_retriever.py   ← TR haber kaynakları
    │   └── kap_event_retriever.py
    ├── agent/
    │   ├── state.py
    │   ├── planner_node.py
    │   ├── router_node.py
    │   ├── critic_node.py
    │   ├── synthesizer_node.py
    │   └── graph.py
    └── api/
        ├── main.py
        ├── auth.py
        └── quota.py
```

---

> Bu araç yatırım tavsiyesi vermez. Tüm cevaplar kamuya açık KAP verilerine dayanır; yatırım kararları kullanıcının sorumluluğundadır.
