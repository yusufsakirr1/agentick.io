# agentick.io — Daily Log

Günlük çalışma kaydı. Her oturumun sonunda güncellenir ve commit edilir.

---

## 2026-07-13 — Pazartesi
**Faz: Faz 1 / Gün 1 — Proje Kurulumu & Planlama**

### Yapılanlar
- Proje fikri netleştirildi: BIST hisseleri için Türkçe agentic AI finansal analist
- Hedef kitle, iş modeli ve rekabet analizi yapıldı (Freemium SaaS, ₺199/ay)
- `uv` ile proje iskeleti oluşturuldu (`pyproject.toml`, `.env`, `.gitignore`, `.python-version`)
- Python 3.12 pinlendi — pyenv'de 3.11.9 vardı, `uv python pin 3.12` ile çözüldü
- `mimari.md` yazıldı: LangGraph Planner → Router → Critic → Synthesizer akışı tasarlandı
- `roadmap.md` yazıldı: 9 fazlı geliştirme planı oluşturuldu
- Qdrant Cloud hesabı açıldı, Frankfurt cluster kuruldu (free tier, 768 boyut, COSINE)
- Teknoloji stack kararları alındı: LangGraph, Claude Sonnet, Qdrant, FastAPI, Next.js, Supabase, Stripe

### Notlar
- Voyage AI embedding için hesap açıldı ama $5 istedi — geçildi, yerel model kullanılacak
- Groq denendi, API key geçersiz geldi — Ollama'ya geçildi
- Anthropic API key alındı, bakiye yüklendi ama henüz görünmüyor

---

## 2026-07-14 — Salı
**Faz: Faz 1 / Gün 2 — KAP Veri Katmanı**

### Yapılanlar
- `kap_client.py` yazıldı: KAP.org.tr'dan faaliyet raporu çekme scripti
- KAP API'sinin bot engeli keşfedildi: 666 status kodu dönüyor, doğrudan erişim bloklandı
- THYAO (Türk Hava Yolları) Mart 2026 YK Faaliyet Raporu KAP sitesinden manuel indirildi
- KAP PDF'lerinin Java wrapper'ına sarılı geldiği keşfedildi (ilk 27 byte gereksiz header)
- `%PDF` byte offsetini bulup wrapper'ı soyma mantığı `kap_client.py`'ye eklendi
- `data/raw/` klasörü oluşturuldu, PDF buraya yerleştirildi
- `dokuman.md` oluşturuldu — oturum notu ve öğrenilen sorunlar kayıt altına alındı

### Çözülen Sorunlar
| Sorun | Çözüm |
|---|---|
| KAP API 666 status kodu (bot engeli) | PDF elle indirildi, ileride Playwright ile otomatize edilecek |
| KAP PDF'leri Java wrapper'ına sarılı | `%PDF` byte offsetinden itibaren kes mantığı eklendi |

---

## 2026-07-15 — Çarşamba
**Faz: Faz 1 / Gün 3 — PDF Chunking & Embedding**

### Yapılanlar
- `pdf_chunker.py` yazıldı: Türkçe PDF temizleme ve chunk'lama pipeline'ı
  - Chunk boyutu: ~500-800 token, %10-15 overlap
  - Bölüm başlıkları (`Finansal Durum`, `Risk Faktörleri` vb.) metadata olarak saklandı
  - THYAO raporu: 25 sayfa → 27 chunk
- Voyage AI embedding denendi — ücretsiz tier çok kısıtlı, $5 istiyor → geçildi
- `paraphrase-multilingual-mpnet-base-v2` (yerel, Türkçe destekli) seçildi ve kuruldu
- `build_vector_index.py` yazıldı: chunk'ları embedding'e dönüştürüp Qdrant'a yükleme
  - 768 boyutlu vektörler, COSINE mesafe
  - Her vektöre `ticker`, `doc_type`, `year`, `page` metadata eklendi
- Qdrant Cloud'a başarıyla yüklendi: 27 vektör, Frankfurt cluster

### Notlar
- Yerel embedding modeli ilk çalıştırmada ~2 GB model indirdi, sonraki çalıştırmalarda cache'den geliyor

---

## 2026-07-16 — Perşembe
**Faz: Faz 1 / Gün 4 — Retriever & CLI Test → FAZ 1 TAMAMLANDI ✅**

### Yapılanlar
- `vector_retriever.py` yazıldı: Qdrant üzerinde semantic search
  - `search()` metodunun Qdrant 1.16.1'de kaldırıldığı keşfedildi → `query_points()` ile değiştirildi
  - Ticker bazlı filtreleme eklendi, ancak payload index olmadan çalışmıyordu → `create_payload_index()` eklendi
- Ollama kuruldu (lokal LLM): `llama3.2` ve `qwen2:7b` modelleri indirildi
- `cli_test.py` yazıldı: uçtan uca test scripti
  - Kullanıcı sorusu → Qdrant semantic search → ilgili chunk'lar → Ollama → Türkçe cevap
- **CLI test başarılı:** "THY'nin 2026 finansal sonuçları?" sorusuna doğru, kaynaklı Türkçe cevap geldi
- `src/__init__.py`, `src/ingestion/__init__.py`, `src/retrievers/__init__.py` oluşturuldu

### Çözülen Sorunlar
| Sorun | Çözüm |
|---|---|
| Qdrant 1.16.1'de `search()` kaldırıldı | `query_points()` kullanıldı |
| Ticker filtresi çalışmıyordu | `create_payload_index()` ile payload index oluşturuldu |

### Faz 1 Çıktı Kriteri ✅
Tek kaynaklı Türkçe sorulara doğru, kaynaklı cevap geliyor.

---

## 2026-07-20 — Pazartesi
**Faz: Faz 2 — SQL Retriever (yfinance + SQLite + text-to-SQL)**

### Yapılanlar
- `src/ingestion/bist_finance_client.py` yazıldı: yfinance → SQLite pipeline
  - `THYAO.IS` gelir tablosu, bilanço, nakit akış ve oranlar çekildi
  - 4 tablo oluşturuldu: `income_statement`, `balance_sheet`, `cash_flow`, `ratios`
  - Her dönem için net marj hesaplanıp `ratios` tablosuna yazıldı
  - yfinance DataFrame erişim hatası bulundu ve düzeltildi (`.get()` yerine `.loc[]` kullanıldı)
- `src/retrievers/sql_retriever.py` yazıldı: text-to-SQL retriever
  - Claude Haiku ile Türkçe soru → SQL dönüşümü
  - SQLite sorgusu çalıştırılıp sonuç `vector_retriever` ile aynı formatta döndürülüyor
- `src/cli_test.py` güncellendi: hybrid RAG (SQL + Vector)
  - Soru tipi keyword analizi ile belirleniyor (sayısal → SQL, yorum → Qdrant, her ikisi → ikisi birden)
- LLM Ollama'dan Claude Sonnet'e geçirildi (API bakiyesi geldi)
- `anthropic` paketi eklendi
- `.gitignore`'a `data/*.db` eklendi

### Test Sonucu ✅
"THYAO'nun son 3 yılda net marjı nasıl değişti?" sorusuna sayısal, kaynaklı cevap:
- 2023: %28,75 → 2024: %15,11 → 2025: %12,08 (düşüş trendi)

### Çözülen Sorunlar
| Sorun | Çözüm |
|---|---|
| yfinance DataFrame'de `.get("Total Revenue", {}).get(col)` NULL dönüyordu | pandas'ta satır erişimi `.loc["Total Revenue", col]` ile yapılır |
| ratios tablosunda sadece bugünün tarihi vardı, tarihçe yoktu | Her gelir tablosu dönemi için ayrı net marj satırı hesaplanıp eklendi |

### Faz 2 Çıktı Kriteri ✅
Türkçe sayısal sorulara SQL üzerinden doğru, kaynaklı cevap geliyor.

---

## 2026-07-17 — Cuma
**Faz: Faz 1 → Faz 2 Geçiş / Dokümantasyon & Altyapı**

### Yapılanlar
- `README.md` sıfırdan yazıldı: proje tanımı, ASCII mimari diagramı, stack tablosu, kurulum adımları, faz durum tablosu
- `daily_log.md` oluşturuldu (bu dosya) — şirket gereksinimi: gün bazlı çalışma kaydı
- Projeye özel git reposu başlatıldı (`git init`) — daha önce üst dizin (`/Users/yusufi`) reposuna gitignore'lanmıştı
- GitHub reposu açıldı: `github.com/yusufsakirr1/agentick.io`
- İlk commit ve push tamamlandı (17 dosya, Faz 1 kodunun tamamı)
- `yfinance` bağımlılığı eklendi (`uv add yfinance`) — Faz 2 SQL Retriever hazırlığı
- BIST ticker formatı doğrulandı: `THYAO.IS` → 329.50 TRY (`.IS` suffix zorunlu)

### Notlar
- yfinance'de BIST hisseleri `.IS` suffix olmadan bulunamıyor (`THYAO` değil `THYAO.IS`)
- Anthropic API bakiyesi görünür olunca `cli_test.py`'deki Ollama → Claude'a çevrilecek

---

## Sıradaki — Faz 2 (SQL Retriever)

- [ ] `bist_finance_client.py` — `yfinance` ile THYAO.IS gelir tablosu, bilanço, F/K, PD/DD
- [ ] `sql_retriever.py` — text-to-SQL: Türkçe soru → SQL → sayısal sonuç
- [ ] SQLite'a finansal veri yazma ve sorgulama testi
- [ ] Çıktı kriteri: "THYAO'nun son 3 yılın net marjı nedir?" sorusuna sayısal, kaynaklı cevap
