# agentick.io — Oturum Notu

Bu dosya, Claude Code ile yapılan çalışmaların özetini tutar.
Her oturuma bu dosyayı atarak nereden devam edeceğimizi belirleriz.

---

## Proje Özeti

**Ürün:** BIST hisseleri için Türkçe AI finansal analist (agentick.io)
**Hedef kitle:** Temel analiz yapmaya çalışan Türk bireysel yatırımcısı
**İş modeli:** Freemium SaaS — 5 sorgu ücretsiz, sonrası aylık ücret
**Rekabet avantajı:** KAP verileri + Türkçe + agentic reasoning (rakip yok bu nişte)

---

## Teknoloji Stack

| Katman | Teknoloji | Durum |
|---|---|---|
| Agent orkestrasyonu | LangGraph | Faz 3'te eklenecek |
| LLM (geliştirme) | Ollama — llama3.2 (lokal) | Aktif |
| LLM (prod) | Claude API (Anthropic) | Bakiye bekleniyor |
| Embedding | sentence-transformers — paraphrase-multilingual-mpnet-base-v2 | Aktif |
| Vector DB | Qdrant Cloud (free tier) | Aktif |
| İlişkisel DB | SQLite (geliştirme) → PostgreSQL/Supabase (prod) | Faz 2'de eklenecek |
| Backend | FastAPI | Faz sonrası |
| Frontend | Next.js + shadcn/ui | Faz 7'de |
| Auth | Supabase Auth | Faz 6'da |
| Ödeme | Stripe | Faz 6'da |

---

## API Keyler (durumu)

| Servis | Durum |
|---|---|
| Anthropic (Claude) | Key var, bakiye yüklendi ama henüz görünmüyor |
| Voyage AI | Hesap açıldı, $5 istedi — geçildi, yerel model kullanılıyor |
| Qdrant Cloud | Aktif, cluster Frankfurt'ta |
| Groq | Denendi, key geçersiz geldi — geçildi |
| Ollama | Lokal kurulu, llama3.2 ve qwen2:7b mevcut |

---

## Klasör Yapısı

```
agentick.io/
├── .env                          ← API keyleri (gitignore'da)
├── .gitignore
├── mimari.md                     ← Tam sistem mimarisi
├── roadmap.md                    ← Faz bazlı checklist
├── dokuman.md                    ← Bu dosya
├── pyproject.toml
├── data/
│   └── raw/
│       └── THYAO_faaliyet_2026.pdf   ← İndirilmiş, işlenmiş
└── src/
    ├── ingestion/
    │   ├── kap_client.py             ← KAP PDF doğrulama (scraping engelli)
    │   ├── pdf_chunker.py            ← Türkçe PDF → chunk
    │   └── build_vector_index.py     ← Qdrant'a embedding yaz
    ├── retrievers/
    │   └── vector_retriever.py       ← Qdrant semantic search
    └── cli_test.py                   ← Uçtan uca test scripti
```

---

## Tamamlanan Fazlar

### ✅ FAZ 1 — Veri Katmanı + Naive RAG

**Ne yapıldı:**
- `uv` ile proje kuruldu
- THYAO Mart 2026 YK Faaliyet Raporu indirildi (KAP API engelledi, manuel indirildi)
- KAP'ın Java wrapper'ı soyuldu (PDF 27 byte offsetten başlıyordu)
- PDF 25 sayfa, 27 chunk'a bölündü
- `paraphrase-multilingual-mpnet-base-v2` (yerel, Türkçe destekli) ile embedding üretildi
- Qdrant Cloud'a yüklendi (768 boyutlu vektör, COSINE mesafe)
- CLI test: "THY'nin 2026 finansal sonuçları?" sorusuna Türkçe cevap geldi

**Öğrenilen sorunlar ve çözümler:**
- KAP API 666 status kodu döndürüyor (bot engeli) → PDF elle indirildi
- KAP PDF'leri Java wrapper'ına sarılı geliyor → `%PDF` offsetinden itibaren kes
- Voyage AI ücretsiz tier çok kısıtlı, $5 istiyor → yerel model kullanıldı
- Qdrant 1.16.1'de `search()` kaldırıldı → `query_points()` kullanılıyor
- Qdrant ticker filtresi için payload index zorunlu → `create_payload_index()` eklendi
- Groq API key'leri çalışmadı → Ollama ile devam edildi
- `.python-version` 3.12 gerektiriyor ama pyenv'de 3.11.9 var → `uv python pin 3.12` ile çözüldü

---

## Devam Edilecek Yer

### 🔄 FAZ 2 — SQL Retriever (SIRADAKI)

**Ne yapılacak:**
- `yfinance` ile THYAO.IS finansal verisi çekilecek (gelir tablosu, bilanço, oranlar)
- SQLite'a yazılacak
- LLM ile text-to-SQL: Türkçe soru → SQL → sonuç
- `sql_retriever.py` oluşturulacak

**Başlamak için:**
```bash
cd /Users/yusufi/Desktop/agentick.io
source .venv/bin/activate
uv add yfinance sqlalchemy pandas
```

**Çıktı kriteri:** "THYAO'nun son 3 yılın net marjı nedir?" sorusuna sayısal, kaynaklı cevap.

---

## Sonraki Fazlar (özet)

| Faz | İçerik |
|---|---|
| 3 | LangGraph agent orkestrasyonu (Planner → Router → Critic → Synthesizer) |
| 4 | Self-critique / retry döngüsü |
| 5 | Synthesizer + KAP kaynak gösterme |
| 6 | Supabase Auth + Freemium kota + Stripe |
| 7 | Next.js frontend + trace paneli |
| 8 | Eval sistemi (20-30 BIST sorusu) |
| 9 | Lansman (Railway deploy + Reddit/Twitter) |

---

## Notlar

- KAP scraping için doğrudan API çalışmıyor. Şimdilik PDF'ler elle indirilip `data/raw/`'a konuluyor. İleride Playwright/Selenium ile otomatize edilebilir.
- Anthropic bakiyesi görünür hale gelince `cli_test.py`'deki Ollama'yı Claude'a çevir.
- GitHub repo açıldı (`yusufsakirr1/agentic.io`) ama push yapılmadı, bekletiliyor.
