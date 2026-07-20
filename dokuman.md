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
| Backend | FastAPI + Uvicorn | Aktif |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS | Aktif |
| Gözlemlenebilirlik | LangSmith | Aktif |

---

## Klasör Yapısı

```
agentick.io/
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── upload.py           # POST /api/upload
│   │   ├── query.py            # POST /api/ask
│   │   ├── fetch_data.py       # POST /api/fetch-data
│   │   └── fetch_news.py       # POST /api/fetch-news
│   └── services/
│       └── pdf_pipeline.py     # PDF → SQLite + Qdrant
├── src/
│   ├── agent/
│   │   ├── state.py
│   │   ├── planner_node.py
│   │   ├── router_node.py      # Auto-fetch mekanizması burada
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
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── components/
│       └── services/
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

---

## Son Durum (Faz 3.5 sonrası)

### Çalışan Özellikler
- LangGraph agent: Planner → Router → Critic → Synthesizer döngüsü
- 3 retriever paralel: SQL + Vektör + Haber
- 6 SQLite tablosu: income_statement, balance_sheet, cash_flow, ratios, dividends, pdf_tables
- Temettü verisi (yfinance .dividends) + temettü verimi hesaplama (dividends JOIN ratios)
- **Auto-fetch:** SQL boş dönünce otomatik yfinance'den çekip tekrar sorgulama
- PDF upload → tablo çıkarma + metin indexleme + yfinance güncelleme
- Sohbet hafızası (localStorage + API)
- BIST-30 tam destek
- LangSmith tracing

### API Endpoint'leri

| Method | Endpoint | Açıklama |
|---|---|---|
| POST | `/api/upload/sync` | PDF yükle ve indexle |
| POST | `/api/ask` | Soru sor, agent yanıtını al |
| POST | `/api/fetch-data` | yfinance verisini SQLite'a çek |
| POST | `/api/fetch-news` | Haber verilerini çek |
| GET | `/api/health` | Sağlık kontrolü |

---

## Gelecek Çalışmalar

Aşağıdaki özellikler sistemin ChatGPT'ye PDF yüklemekten **gerçek farkını** ortaya koyacak ve monetize edilebilir hale getirecek geliştirmelerdir.

### 1. Çoklu Şirket Karşılaştırma
Tek seferde birden fazla hisseyi karşılaştırabilme. Örnek sorular:
- "TUPRS vs PETKM vs ASELS son 3 yıl kârlılık karşılaştırması"
- "BIST-30'da en yüksek temettü verimi veren 5 hisse"
- "THYAO ve PGSUS'un borç/özkaynak oranlarını karşılaştır"

**Gerekli:** Router'ın multi-ticker desteği, SQL retriever'da cross-ticker JOIN sorguları.

### 2. Otomatik Screening ve Alert
Kullanıcının belirlediği kriterlere göre hisse taraması ve bildirim. Örnek:
- "Temettü verimi %5 üzeri, borç/özkaynak %50 altı BIST hisseleri bul"
- "P/E oranı 10'un altındaki hisseler"
- "Net marjı son 2 yılda artan şirketler"

**Gerekli:** Tüm BIST-30 hisseleri için periyodik veri çekme (cron/scheduler), screening query engine.

### 3. Zaman Serisi Takibi ve Bildirim
Hisse takibi ve önemli olay bildirimi. Örnek:
- "TUPRS'u takip et, temettü açıklanınca bildir"
- "THYAO fiyatı 350 TL'yi geçerse uyar"
- "Takip listeme ASELS ve FROTO ekle"

**Gerekli:** Kullanıcı bazlı watchlist, background scheduler, push notification (email/webhook).

### 4. Portföy Analizi
Kullanıcının portföyünü yükleyip analiz edebilmesi. Örnek:
- "5 hissemi yükledim, portföyümün sektör dağılımı ne?"
- "Portföyümün toplam temettü geliri ne kadar?"
- "Portföy risk dağılımım nasıl, çok mu yoğunlaşmış?"

**Gerekli:** Portföy veri modeli, sektör/endüstri sınıflandırma, ağırlıklı metrik hesaplama.

### 5. BIST'e Özel Domain Bilgisi ve KAP Entegrasyonu
ChatGPT genel amaçlı — agentick BIST'e özel. Fark yaratan özellikler:
- KAP özel durum açıklamaları (temettü, sermaye artırımı, birleşme) otomatik çekme
- BIST endeks değişiklikleri takibi
- Türk muhasebe standartlarına göre rasyo hesaplama
- Halka arz takibi

**Gerekli:** KAP veri dağıtım sözleşmesi veya alternatif veri kaynakları (Finnet, Matriks, İş Yatırım API).

### 6. Altyapı ve Ürünleştirme
- Auth — Supabase ile kullanıcı girişi, aylık sorgu kotası
- Deployment — Railway (backend) + Vercel (frontend)
- Eval sistemi — 30 BIST sorusu ile doğruluk metrikleri
- Stripe entegrasyonu — ₺199/ay abonelik

---

## Devam Edilecek Yer

Gelecek çalışmalar listesinden **Çoklu Şirket Karşılaştırma** en düşük eforla en yüksek değeri verecek özellik. Router'a multi-ticker desteği eklemek ve tüm BIST-30 için periyodik veri çekmekle başlanabilir.
