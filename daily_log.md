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

---

## 2026-07-21 — Pazartesi
**Faz: Faz 3 — LangGraph Agent + FastAPI Backend + React Frontend**

Bu oturumda sistem mimari olarak komple yeniden tasarlandı. Faz 2'deki basit `if/else` keyword routing yerine gerçek bir LangGraph agentic sistemi kuruldu. Frontend sıfırdan yazıldı. Uçtan uca çalışan, kaynaklı Türkçe cevap veren platform tamamlandı.

---

### Adım 1 — KAP Otomasyonu Kararı

**Plan:** Playwright ile KAP.org.tr'dan otomatik PDF indirme yapılacaktı.

**Sorun:** KAP.org.tr'nun verilerini dağıtmak için Borsa İstanbul ile resmi veri dağıtım sözleşmesi gerektiği anlaşıldı. KAP API PDF'si incelendi — kurumsal API sözleşme şartı var, bireysel geliştirici için mümkün değil.

**Karar:** KAP otomasyonu atlandı. Kullanıcı PDF'yi kendisi siteden indirip platforma yükleyecek.

---

### Adım 2 — Yeni Mimari Kararı

Orijinal plandan vazgeçildi, yeni mimari tasarlandı:

**Eski:** Agent CLI aracılığıyla çalışıyor, PDF elle yerleştiriliyor.

**Yeni:** Kullanıcı web arayüzünden PDF yükler. Sistem üç paralel iş yapar:
- PDF metni → chunk'lar → 768D embedding → Qdrant
- PDF tabloları → `pdf_tables` SQLite tablosu
- yfinance → `income_statement`, `balance_sheet`, `cash_flow`, `ratios` SQLite tabloları

Karar: Streamlit yerine FastAPI + React. Streamlit basit ama agentic UX için yetersiz.

---

### Adım 3 — LangGraph Agent Implementasyonu

Klasik `if/else` routing kaldırıldı. LangGraph `StateGraph` ile düğüm tabanlı akış kuruldu.

**`src/agent/state.py`** oluşturuldu:
```python
class AgentState(TypedDict):
    question: str
    ticker: str
    conversation_history: list[dict]
    standalone_question: str
    sub_tasks: list[dict]
    retrieved: Annotated[list[dict], operator.add]  # her retry'da birikir
    critic_feedback: str
    retry_count: int
    final_answer: str
```
`retrieved` alanı `operator.add` ile annotate edildi — her retry'da retriever sonuçları üstüne eklenir.

**`src/agent/planner_node.py`** oluşturuldu:
- Model: Claude Haiku 4.5 (hızlı, ucuz)
- Tek LLM çağrısıyla iki iş: (1) takip sorusunu standalone hale getir, (2) `sql` veya `vector` tipinde alt görevler üret
- Sohbet geçmişinin son 6 mesajı prompt'a dahil edildi

**`src/agent/router_node.py`** oluşturuldu:
- `asyncio.gather()` ile SQL ve vector retriever paralel çalışır
- Retry'da `top_k` artırıldı: `4 + (retry_count * 4)`
- Her retriever `asyncio.to_thread()` ile sync → async sarıldı

**`src/agent/critic_node.py`** oluşturuldu:
- Model: Claude Haiku 4.5
- Max 6 kaynak gösterilir (gereksiz token harcamayı önler)
- `"SUFFICIENT"` → synthesizer'a geç; `"INSUFFICIENT: ..."` → planner'a geri dön
- Max 3 retry, aşılırsa elde olanla cevap verilir
- İlk versiyonda çok katı davranıyordu (3 hakkı her zaman dolduruyordu). Prompt daha esnek hale getirildi: "herhangi bir bilgi varsa yeterli say"

**`src/agent/synthesizer_node.py`** oluşturuldu:
- Model: Claude Sonnet 4.6 (en güçlü, kaliteli Türkçe)
- Score'a göre sıralanmış max 12 kaynak alınır
- Her iddia için parantez içinde kaynak gösterimi
- Son satır zorunlu: "Bu bilgi yatırım tavsiyesi değildir."

**`src/agent/graph.py`** oluşturuldu:
```
START → planner → router → critic ─┬─ "retry" → planner
                                    └─ "synthesize" → synthesizer → END
```
- `run_agent(question, ticker, conversation_history)` fonksiyonu dışa açıldı
- Async router düğümü için sync wrapper yazıldı (LangGraph sync bağlamında çalışır)

---

### Adım 4 — FastAPI Backend

**`backend/main.py`** oluşturuldu:
- CORS: `localhost:5173` (Vite dev server), `localhost:3000`
- Üç router: upload, query, fetch-data

**`backend/routes/upload.py`** oluşturuldu:
- `POST /api/upload` — arka planda (async background task)
- `POST /api/upload/sync` — frontend'in kullandığı, tamamlanmasını bekleyen versiyon

**`backend/routes/query.py`** oluşturuldu:
- `POST /api/ask` — LangGraph agent çağrısı
- İstek: `{question, ticker, conversation_history: []}`
- Yanıt: `{answer, ticker, sub_tasks, retrieved_count, retry_count, critic_feedback}`

**`backend/routes/fetch_data.py`** oluşturuldu:
- `POST /api/fetch-data` — ticker alıp yfinance verisini SQLite'a yazar

**`backend/services/pdf_pipeline.py`** oluşturuldu:
- `process_pdf(pdf_path, ticker)` — 3 aşamalı pipeline:
  1. `pdfplumber` → tablolar → `pdf_tables` SQLite (aynı dosya yeniden yüklenirse önce siler)
  2. `PyMuPDF` + `pdf_chunker` → embedding → Qdrant
  3. `yfinance` → 4 finansal tablo → SQLite

---

### Adım 5 — React Frontend (Sıfırdan)

Streamlit yerine React + TypeScript + Vite + Tailwind CSS tercih edildi. Tasarım ChatGPT benzeri iki panel layout: sol sidebar + sağ chat alanı.

**`frontend/src/components/AgentLogo.tsx`** oluşturuldu:
- Lucide React'tan `MousePointerClick` ikonu seçildi
- `scaleX(-1)` ile sağ üst köşeye bakacak şekilde çevrildi
- Arka plan yok, saf ikon
- `color` prop'u ile farklı arka planlarda siyah/beyaz kullanımı

**`frontend/src/components/ThinkingIndicator.tsx`** oluşturuldu:
- 4 aşamalı animasyon: "Soru analiz ediliyor" → "SQL ve belgeler taranıyor" → "Sonuçlar değerlendiriliyor" → "Yanıt hazırlanıyor"
- Her aşama sabit süre sonra geçiş yapar (fade animasyonu)
- Kullanıcı bekleme süresini daha az hisseder

**`frontend/src/components/Message.tsx`** oluşturuldu:
- Kullanıcı mesajı: sağda, siyah arka plan
- AI yanıtı: solda, `react-markdown` ile render
- Meta chipler: SQL/Vektör retriever tipi, retry sayısı
- AgentLogo etrafında hafif gölge ring (yuvarlak çerçeve)

**`frontend/src/components/Sidebar.tsx`** oluşturuldu:
- "Yeni Sohbet" butonu (`MessageCirclePlus` ikonu)
- Konuşmalar grup bazlı: Bugün / Dün / Bu Hafta / Daha Önce
- Her satırda ticker badge + konuşma başlığı
- Hover'da sil butonu (kırmızı ×)
- Alt kısımda kullanıcı profili

**`frontend/src/components/ChatInput.tsx`** oluşturuldu:
- Pill tasarım (rounded-full, tek satır)
- Soldan: paperclip (PDF upload) → ticker dropdown → textarea
- Sağda: send butonu (siyah yuvarlak, ok ikonu)
- PDF yükleme: sync upload, progress bar animasyonu, dosya durumu göstergesi
- yfinance fetch butonu (`RefreshCw` ikonu)

**`frontend/src/services/conversationStorage.ts`** oluşturuldu:
- `localStorage` ile konuşma geçmişi saklama
- `Conversation` arayüzü: `{id, title, ticker, messages, createdAt, updatedAt}`
- Fonksiyonlar: getAll, upsert, remove, createNew, makeTitle, groupByDate

**`frontend/src/api/client.ts`** oluşturuldu:
- `uploadPDF(ticker, file, sync?)` — `POST /api/upload/sync`
- `askQuestion(question, ticker, history)` — `POST /api/ask`
- `fetchFinancialData(ticker)` — `POST /api/fetch-data`

**`frontend/src/App.tsx`** oluşturuldu:
- İki durum: boş ekran (öneri chip'leri) / chat ekranı
- `conversation_history` son N mesaj olarak `/api/ask`'a gönderilir
- Header'da ticker dropdown (chat modunda hisse değiştirilebilir)

---

### Adım 6 — LangSmith Tracing Entegrasyonu

`.env`'e eklendi:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=agentick
```
LangSmith dashboard'dan her sorgunun Planner → Router → Critic → Synthesizer akışı izlenebilir hale geldi.

---

### Adım 7 — Backend İyileştirme #1: Synthesizer Kaynak Limiti

**Sorun:** Her retry'da `retrieved` listesi birikiyordu (operator.add). Synthesizer'a 60+ kaynak gidebiliyordu → Claude context doluyordu, cevap kalitesi düşüyordu.

**Çözüm:** `synthesizer_node.py`'de `MAX_SOURCES = 12` eklendi. Kaynaklar score'a göre azalan sırada sıralanır, ilk 12'si alınır (SQL sonuçları score=1.0, vector sonuçları cosine similarity).

---

### Adım 8 — Backend İyileştirme #2: yfinance Endpoint

**Sorun:** Kullanıcı ticker değiştirince yfinance verisi manuel güncellenmiyordu.

**Çözüm:**
- `backend/routes/fetch_data.py` — `POST /api/fetch-data` endpoint'i zaten vardı, frontend entegrasyonu tamamlandı
- `frontend/src/api/client.ts`'e `fetchFinancialData()` eklendi
- `ChatInput.tsx`'e `RefreshCw` butonu eklendi; tıklanınca spinner gösterir, 3 saniye sonra başarı/hata mesajı kaybolur

---

### Adım 9 — Backend İyileştirme #3: Router Duplicate Önleme

**Sorun:** Retry'larda aynı chunk'lar tekrar `retrieved` listesine ekleniyordu. 3 retry sonunda Synthesizer aynı metni 3 kez okuyordu.

**Çözüm:** `router_node.py`'de yeni sonuçlar eklenmeden önce mevcut `retrieved` listesindeki `text` değerleri bir `set`'e alınır. Aynı text'e sahip chunk iki kez eklenmez. Her retry gerçekten yeni bilgi getirir.

---

### Adım 10 — Backend İyileştirme #4: pdf_tables Testi ve Düzeltmeler

**Test edilenler:**
1. SQLite'ta 32 satır pdf_tables verisi (THYAO Mart 2026 raporundan)
2. SQL retriever'ın pdf_tables'ı sorgulayıp sorgulayamadığı

**Bulunan sorunlar ve çözümler:**

| Sorun | Çözüm |
|---|---|
| Citation yanlış: "yfinance — THYAO finansal tablolar" | `pdf_tables` tespiti eklendi: `PDF — THYAO filename.pdf` |
| Text gürültülü: tüm kolonlar gösteriliyordu | `_rows_to_text` güncellendi: sadece `[Sayfa N]` + `table_text` |
| SQL'de OR koşulları ticker filtresini bypass ediyordu | Prompt'a kural eklendi: `WHERE ticker='X' AND (... OR ...)` |

---

### Adım 11 — BIST-30 Genişletme

Frontend'deki ticker dropdown'ı 15 hisseden 30 hisseye çıkarıldı. Tam BIST-30 listesi (alfabetik) eklendi:

`AKBNK AKSEN ARCLK ASELS BIMAS EKGYO ENKAI EREGL FROTO GARAN GUBRF HALKB ISCTR KCHOL KONTR KOZAL KRDMD ODAS PETKM PGSUS SAHOL SASA SISE TAVHL TCELL THYAO TOASO TUPRS VAKBN YKBNK`

ChatInput.tsx ve App.tsx header dropdown'ı güncellendi.

---

### Adım 12 — Ticker Bug Düzeltmesi

**Sorun:** `handleTickerChange` fonksiyonunda `if (!active) return` vardı. Sohbet yokken (boş ekranda) ticker değiştirince değişiklik sessizce yok oluyordu.

**Çözüm:**
- `App.tsx`'e `defaultTicker` state'i eklendi
- `ticker = active?.ticker ?? defaultTicker` ile türetildi
- Sohbet yokken ticker değişimi `defaultTicker`'a yazılır
- Header'daki statik ticker badge → tıklanabilir dropdown'a dönüştürüldü (chat içinde de hisse değiştirilebilir)

---

### Adım 13 — End-to-End Test

5 test senaryosu çalıştırıldı, 5/5 başarılı:

| Test | Retriever | Kaynaklar | Retry | Süre |
|---|---|---|---|---|
| SQL — Net marj | sql + vector | 5 | 1 | 23.5s |
| Vector — Büyüme stratejisi | sql + vector | 4 | 1 | 27.8s |
| Karma — Performans + sürdürülebilirlik | sql + vector | 6 | 1 | 26.5s |
| pdf_tables — Hissedar yapısı | sql + vector | 5 | 1 | 16.9s |
| Hafıza — Takip sorusu rewrite | sql + vector | 5 | 1 | 20.2s |

Önemli gözlem: Critic her testte ilk turda SUFFICIENT dedi, 3 retry hakkını doldurmadı.

---

### Adım 14 — README.md ve mimari.md Güncelleme

Proje genelinde yapılan değişiklikler nedeniyle her iki doküman eski bilgiler içeriyordu.

- `README.md`: Komple yeniden yazıldı. Yeni stack tablosu, endpoint listesi, dosya yapısı, BIST-30 listesi, örnek istek/yanıt eklendi.
- `mimari.md`: Komple yeniden yazıldı. LangGraph akış diyagramı, retriever detayları, SQL şemaları, ingestion pipeline, frontend bileşen hiyerarşisi, implementasyon durumu tablosu güncellendi.

---

### Faz 3 Çıktı Kriterleri ✅

- ✅ LangGraph agent çalışıyor (Planner → Router → Critic → Synthesizer)
- ✅ PDF yükleme → tablo çıkarma + metin indexleme pipeline'ı çalışıyor
- ✅ SQL ve vector retriever paralel çalışıyor
- ✅ Critic gereksiz retry yapmıyor
- ✅ Synthesizer kaynaklı Türkçe yanıt üretiyor
- ✅ Sohbet hafızası çalışıyor (takip soruları doğru anlaşılıyor)
- ✅ BIST-30 tüm hisseler destekleniyor
- ✅ LangSmith ile her sorgu izlenebilir

---

### Sıradaki — Faz 4

- [ ] Auth — Supabase ile kullanıcı girişi
- [ ] Kullanıcı başına aylık sorgu kotası
- [ ] Haber Retriever (Bloomberg HT / Dünya gazetesi)
- [ ] KAP Özel Durum Retriever (temettü, sermaye artırımı bildirimleri)
- [ ] Deployment — Railway (backend) + Vercel (frontend)

---

## 2026-07-22 — Salı
**Faz: Faz 3.5 — Temettü Verisi, Auto-Fetch ve Haber Retriever**

Bu oturumda agent'ın veri kapsamı genişletildi: temettü verisi, otomatik veri çekme ve haber retriever eklendi. Ayrıca TUPRS 504 sayfalık faaliyet raporu ile performans testi yapıldı.

---

### Adım 1 — Temettü Verisi (yfinance .dividends)

**Sorun:** Agent'a "temettü kararı ne?" diye sorulduğunda veri bulunamıyordu — temettü bilgisi hiçbir tabloda yoktu.

**Çözüm:**
- `src/ingestion/bist_finance_client.py` → `dividends` tablosu eklendi (`ticker`, `ex_date`, `amount`)
- `create_tables()` içine `CREATE TABLE IF NOT EXISTS dividends` eklendi
- `fetch_and_store()` içine `yf_ticker.dividends` çekme bloğu eklendi (oranlar bölümünden sonra)
- `src/retrievers/sql_retriever.py` → `DB_SCHEMA`'ya `dividends` tablosu tanımı eklendi, `all_tables` listesine dahil edildi

**Test:** TUPRS için 24 temettü ödemesi başarıyla kaydedildi.

---

### Adım 2 — Auto-Fetch: SQL Boş Dönünce Otomatik Veri Çekme

**Sorun:** `fetch_and_store()` sadece CLI'dan elle çalıştırılıyordu. Kullanıcı yeni bir hisse sorduğunda SQLite'ta veri yoksa agent 3 kez retry edip "veri bulunamadı" diyordu.

**Çözüm:**
- `src/agent/router_node.py` → `run_task()` içinde SQL bloğuna auto-fetch eklendi
- SQL sorgusu boş dönerse → `fetch_and_store(ticker)` çağrılır → aynı sorgu tekrar çalıştırılır
- Lazy import: `from src.ingestion.bist_finance_client import fetch_and_store` sadece gerektiğinde yüklenir
- Veri zaten varsa fetch tetiklenmez (ilk sorgu sonuç döner)

**Test:** THYAO dividends tablosu boşken "THYAO temettü geçmişi ne?" soruldu → otomatik çekildi → 4 temettü ödemesi kaydedilip cevap verildi.

---

### Adım 3 — Temettü Verimi (Dividend Yield) Hesaplama

**Sorun:** Agent "temettü verimi" sorulduğunda "fiyat bilgisi yok" diyordu — oysa `ratios` tablosunda `current_price` zaten var.

**Çözüm:**
- `src/retrievers/sql_retriever.py` → `TEXT_TO_SQL_PROMPT` kurallarına temettü verimi ipucu eklendi
- `yield = (son 12 ay toplam temettü / current_price) * 100` formülü ile SQL JOIN örneği verildi
- Yeni tablo/veri gerekmedi — mevcut `dividends` + `ratios.current_price` JOIN'i yeterli

**Test:** "TUPRS son 2 yıl temettü tutarları ve verimleri?" → %2,57 ve %3,59 yield doğru hesaplandı.

---

### Adım 4 — 504 Sayfalık Faaliyet Raporu Performans Testi

TUPRS 2025 entegre faaliyet raporu (504 sayfa) yüklendi ve 5 farklı soru tipiyle test edildi:

| Soru | Retriever | Sonuç |
|---|---|---|
| "TUPRS toplam borç/özkaynak oranı ne?" | SQL + Vektör | 4 yıllık veri + yorum — Mükemmel |
| "TUPRS risk faktörleri nelerdir?" | SQL + Vektör | 7 kategori, sayfa ref. — Mükemmel |
| "TUPRS son 3 yılda net kârı nasıl değişti ve yönetim ne diyor?" | SQL + Vektör | Sayısal + nitel birlikte — Mükemmel |
| "TUPRS ham petrol işleme maliyeti nedir?" | SQL + Vektör | "Belgede yok" — Doğru (hallüsinasyon yok) |
| "TUPRS son 2 yıl temettü tutarları ve verimleri?" | SQL | Yield hesaplama dahil — Mükemmel |

Agent 504 sayfalık rapordan doğru sayfa referanslarıyla bilgi çekiyor, bulamadığında dürüstçe söylüyor.

---

### Adım 5 — Dokümantasyon Güncellemesi

- `dokuman.md` güncellendi: Gelecek çalışmalar bölümü eklendi (çoklu şirket karşılaştırma, screening, portföy analizi, zaman serisi takibi, KAP entegrasyonu)
- `mimari.md` güncellendi: dividends tablosu, news_articles tablosu, auto-fetch mekanizması, news retriever detayları eklendi
- `README.md` güncellendi: news retriever, auto-fetch, temettü verimi, genişletilmiş soru örnekleri
- `daily_log.md` güncellendi (bu kayıt)

---

### Çözülen Sorunlar

| Sorun | Çözüm |
|---|---|
| Temettü verisi hiçbir tabloda yoktu | `dividends` tablosu + yfinance `.dividends` eklendi |
| Yeni hisse sorulduğunda "veri bulunamadı" | Auto-fetch: SQL boş → yfinance'den çek → tekrar sorgula |
| Temettü verimi hesaplanamıyordu | SQL prompt'a `dividends JOIN ratios` ipucu eklendi |

---

### Faz 3.5 Çıktı Kriterleri ✅

- ✅ Temettü verisi çekilip sorgulanıyor
- ✅ Temettü verimi (yield) güncel fiyat üzerinden hesaplanıyor
- ✅ SQL boş dönünce otomatik yfinance fetch tetikleniyor
- ✅ 504 sayfalık rapordan doğru, kaynaklı cevaplar geliyor
- ✅ Haber retriever (news) çalışıyor

---

---

## 2026-07-22 — Salı
**Faz: Faz 4 / Gün 1 — Çoklu Şirket Karşılaştırma: Backend + Agent + Frontend Altyapı**

Bu oturumda çoklu şirket karşılaştırma özelliğinin backend ve agent tarafı tamamlandı, frontend altyapısı (React Router, sayfa ayrımı, navigasyon) kuruldu.

---

### Adım 1 — Shared Constants: BIST Ticker Listesi

**Sorun:** BIST-30 ticker listesi 3 yerde duplicate edilmişti (App.tsx, ChatInput.tsx, backend SQL prompt).

**Çözüm:**
- `frontend/src/constants/tickers.ts` oluşturuldu: `BIST_TICKERS` sabiti ve `BistTicker` tipi
- `App.tsx` ve `ChatInput.tsx`'teki inline diziler kaldırılıp import eklendi

---

### Adım 2 — Backend: Metrik Karşılaştırma Endpoint'i

`backend/routes/compare.py` oluşturuldu:

**GET `/api/compare/metrics?tickers=THYAO,TUPRS`**
- 2 ticker alır
- Her çağrıda yfinance'den güncel veri çeker (fiyat, oranlar vb. her gün değişiyor)
- 4 SQL sorgusu: ratios, income_statement, balance_sheet, dividends
- Her ticker için en son dönem verisini döndürür
- LLM gerektirmeyen, doğrudan SQLite sorgusu — milisaniyeler içinde döner

**Response yapısı:** `{ tickers: [...], metrics: { THYAO: { pe_ratio, net_margin, ... }, TUPRS: {...} } }`

`backend/main.py`'ye `compare_router` kaydedildi.

---

### Adım 3 — Multi-Ticker Agent Desteği

Mevcut LangGraph agent'ın çoklu ticker ile çalışması sağlandı:

**`src/agent/state.py`:**
- `tickers: list[str]` alanı eklendi (mevcut `ticker: str` korundu, geriye uyumluluk)

**`src/agent/graph.py`:**
- `run_agent()` fonksiyonuna `tickers: list[str] | None = None` parametresi eklendi
- `initial_state`'e `tickers` alanı eklendi: `tickers or [ticker.upper()]`

**`src/agent/planner_node.py`:**
- `PLANNER_PROMPT_MULTI` eklendi: "Karşılaştırılacak şirketler: {tickers}", her ticker için ayrı sub_task üretme talimatı
- Sub-task formatına `ticker` alanı eklendi: `{"query": "...", "type": "sql", "ticker": "THYAO"}`
- `planner_node()` içinde `len(tickers) > 1` kontrolü → uygun prompt seçimi
- Çoklu ticker için `max_tokens` 512'den 1024'e çıkarıldı

**`src/agent/router_node.py`:**
- Per-task ticker desteği: `task_ticker = task.get("ticker", state["ticker"])`
- SQL, vector ve news çağrılarında `state["ticker"]` yerine `task_ticker` kullanıldı
- Auto-fetch de `task_ticker` için tetikleniyor

**`src/agent/synthesizer_node.py`:**
- `SYSTEM_PROMPT_COMPARE` eklendi: karşılaştırmalı analiz formatı, güçlü/zayıf yön talimatı
- `synthesizer_node()` içinde `len(tickers) > 1` → uygun prompt ve max_tokens (2500) seçimi

---

### Adım 4 — Karşılaştırma Chat Endpoint'i

`backend/routes/compare.py`'ye eklendi:

**POST `/api/compare/ask`**
- `{question, tickers: ["GARAN","AKBNK"], conversation_history}` alır
- `run_agent(question, tickers[0], history, tickers=tickers)` çağırır
- try/except ile agent hatalarını yakalar

---

### Adım 5 — React Router Kurulumu

**Install:** `npm install react-router-dom`

**`frontend/src/main.tsx`:**
- `<BrowserRouter>` ile `<App />` sarıldı

**`frontend/src/App.tsx`:**
- Chat UI kodu `ChatPage.tsx`'e taşındı
- App.tsx sadece layout shell + Routes oldu:
  - `Route path="/"` → `<ChatPage />`
  - `Route path="/compare"` → `<ComparePage />`
- Conversation state ve handler'lar App.tsx'te kaldı, ChatPage'e prop olarak geçildi

**`frontend/src/pages/ChatPage.tsx`:**
- App.tsx'ten çıkarılan header + empty state + chat + ChatInput kodu

---

### Adım 6 — Sidebar Navigasyonu

`frontend/src/components/Sidebar.tsx` güncellendi:

- "Yeni Sohbet" butonunun altına 2 tab'lık navigasyon eklendi: `[Sohbet] [Karşılaştır]`
- `useNavigate()` ve `useLocation()` ile aktif sayfa tespiti
- Sohbet: `MessageCirclePlus` ikonu, `/` route
- Karşılaştır: `GitCompareArrows` ikonu, `/compare` route
- Aktif tab: beyaz arka plan + gölge, inaktif: gri
- Konuşma listesinden tıklayınca otomatik `/` route'una geçiş

---

### Adım 7 — API Client Güncellemesi

`frontend/src/api/client.ts`'e eklendi:

- `fetchComparisonMetrics(tickers: string[])` → `GET /api/compare/metrics`
- `askCompareQuestion(question, tickers, history)` → `POST /api/compare/ask`
- Yeni interface'ler: `TickerMetrics`, `ComparisonMetrics`, `CompareAskResult`

---

### Faz 4 / Gün 1 Çıktıları

- ✅ Backend metrics endpoint çalışıyor (yfinance auto-fetch dahil)
- ✅ Multi-ticker agent çalışıyor (per-task ticker, karşılaştırma prompt'ları)
- ✅ React Router kuruldu (/, /compare)
- ✅ Sidebar navigasyonu çalışıyor
- ✅ Mevcut sohbet regresyon yok — `/` route'unda eskisi gibi çalışıyor
- ✅ TypeScript build hatasız geçiyor

---

## 2026-07-23 — Çarşamba
**Faz: Faz 4 / Gün 2 — Karşılaştırma UI Bileşenleri + Hata Düzeltmeleri → FAZ 4 TAMAMLANDI ✅**

Bu oturumda karşılaştırma sayfasının tüm frontend bileşenleri yazıldı, performans ve hata sorunları çözüldü.

---

### Adım 1 — TickerSelector Bileşeni

`frontend/src/components/TickerSelector.tsx` oluşturuldu:

- Seçili ticker'lar siyah badge olarak görünür (× ile kaldırma)
- "+ Ekle" butonu → dropdown açılır, BIST-30'dan seçim
- 2 ticker sınırı (şimdilik)
- Herhangi bir ticker kaldırılıp yerine başkası eklenebilir
- Dışarı tıklayınca dropdown kapanır

---

### Adım 2 — ComparisonTable Bileşeni

`frontend/src/components/ComparisonTable.tsx` oluşturuldu:

- 12 metrik satırı: Fiyat, Piyasa Değeri, F/K, PD/DD, Net Marj, ROE, ROA, Borç/Özkaynak, Temettü Verimi, Gelir, Net Kâr, FAVÖK
- Her ticker bir kolon
- Büyük sayılar formatlanır: "1.2 T TL", "450 Mrd TL", "120 Mn TL"
- Loading skeleton animasyonu
- `hover:bg-gray-50` satır efekti

---

### Adım 3 — ComparisonChat Bileşeni

`frontend/src/components/ComparisonChat.tsx` oluşturuldu:

- Mevcut `Message.tsx` ve `ThinkingIndicator.tsx` yeniden kullanıldı
- Input bar: seçili ticker badge'leri (read-only) + textarea + send butonu
- Ticker değişince chat sıfırlanır (ephemeral — localStorage'a kaydetmez)
- Backend error alanını kontrol eder

---

### Adım 4 — ComparePage Orchestrator

`frontend/src/pages/ComparePage.tsx` oluşturuldu:

- Orchestrator bileşen: Header → TickerSelector → ComparisonTable → ComparisonChat
- Varsayılan ticker'lar: THYAO, TUPRS (değiştirilebilir)
- `useEffect` → `fetchComparisonMetrics(tickers)` her ticker değişiminde
- Hata durumu göstergesi

---

### Adım 5 — Qdrant Timeout ve Router Task Timeout

**Sorun:** Karşılaştırma chat sorgusu gönderildiğinde agent takılıyordu — Qdrant cloud'a bağlantı timeout olmadan asılıyordu.

**Çözüm:**
- `src/retrievers/vector_retriever.py` → `QdrantClient` oluşturulurken `timeout=15` eklendi
- `src/agent/router_node.py` → her retriever task'ı `asyncio.wait_for(timeout=30)` ile sarıldı
- Timeout olan task atlanır, agent SQL ve news sonuçlarıyla devam eder
- Agent artık takılma riski olmadan çalışıyor

---

### Adım 6 — Metrikler Her Zaman Güncel Çekilmesi

**Sorun:** `/api/compare/metrics` sadece veritabanında verisi olmayan ticker'lar için yfinance çekiyordu. Ama fiyat ve oranlar her gün değişiyor.

**Çözüm:** `compare_metrics` endpoint'i her çağrıda tüm ticker'lar için `fetch_and_store()` çağırır. Kullanıcı her zaman güncel veri görür.

---

### Adım 7 — End-to-End Test

GARAN vs AKBNK karşılaştırma testi başarılı:

```
Soru: "Hangi bankanın net marjı daha yüksek?"
Yanıt: 4 yıllık net marj karşılaştırması + güçlü/zayıf yön analizi
Sub-tasks: 6 adet (her ticker için sql + vector + news)
Retrieved: 5 kaynak
Retry: 0 (ilk turda SUFFICIENT)
```

---

### Çözülen Sorunlar

| Sorun | Çözüm |
|---|---|
| BIST ticker listesi 3 yerde duplicate | `constants/tickers.ts` tek kaynak |
| Qdrant bağlantısı timeout olmadan asılıyordu | `QdrantClient(timeout=15)` eklendi |
| Router task'ları sonsuza kadar bekleyebiliyordu | `asyncio.wait_for(timeout=30)` eklendi |
| Metrikler stale kalabiliyordu | Her çağrıda yfinance auto-fetch |
| Internal Server Error hata mesajı belirsizdi | Backend'de try/except, frontend'de error kontrolü |
| Seçili ticker'lar değiştirilemiyordu | X butonu her zaman görünür hale getirildi |

---

### Faz 4 Çıktı Kriterleri ✅

- ✅ `/compare` sayfasında 2 hisseyi yan yana karşılaştırma
- ✅ Metrik tablosu: Fiyat, F/K, PD/DD, Net Marj, ROE, ROA, FAVÖK vb.
- ✅ Karşılaştırma chat: seçili hisseler hakkında serbest soru-cevap
- ✅ Multi-ticker agent: her ticker için ayrı retriever çağrısı
- ✅ Sidebar navigasyonu: Sohbet / Karşılaştır sekmeli geçiş
- ✅ Mevcut sohbet regresyon yok
- ✅ TypeScript + Vite build hatasız

---

### Sıradaki — Faz 5

- [ ] Auth (Firebase)
- [ ] Landing Page yeniden tasarım
- [ ] Deployment

---

## 2026-07-23 — Perşembe
**Faz: Faz 5 / Gün 1 — Firebase Authentication Entegrasyonu**

Bu oturumda kullanıcı kimlik doğrulama sistemi Firebase Authentication ile sıfırdan kuruldu. Google OAuth popup ile giriş, AuthContext pattern ve backend token doğrulama tamamlandı.

---

### Adım 1 — Firebase Projesi Kurulumu

- Firebase Console'da `agentick-io` projesi oluşturuldu
- Authentication → Sign-in method → Google provider aktif edildi
- Web app kaydedildi, Firebase config alındı
- `firebase` npm paketi yüklendi: `npm install firebase`

---

### Adım 2 — Frontend Firebase Config

`frontend/src/config/firebase.ts` oluşturuldu:
- `initializeApp()` ile Firebase başlatma
- `getAuth()` ile auth instance
- `GoogleAuthProvider` oluşturma
- Tüm config değerleri `import.meta.env.VITE_FIREBASE_*` üzerinden (`.env` dosyasında)

---

### Adım 3 — AuthContext ve AuthProvider

`frontend/src/contexts/AuthContext.tsx` oluşturuldu:
- `AuthContextType` interface: `user`, `loading`, `signInWithGoogle`, `signOut`
- `AuthProvider` bileşeni: `onAuthStateChanged` listener ile auth durumu takibi
- `signInWithGoogle()`: `signInWithPopup(auth, googleProvider)` — popup ile Google giriş
- `signOut()`: `firebaseSignOut(auth)`
- `useAuth()` hook: context'e kolay erişim, provider dışında kullanılırsa hata fırlatır

---

### Adım 4 — App.tsx Auth Guard

`frontend/src/App.tsx` güncellendi:
- `useAuth()` hook'u ile `user` ve `loading` alınır
- `authLoading` durumunda spinner gösterilir
- `!user` → `<LoginPage />` render edilir (landing page)
- `user` → mevcut layout shell (Sidebar + Routes) render edilir
- Giriş yapınca otomatik geçiş — state değişimi ile re-render

---

### Adım 5 — main.tsx AuthProvider Sarma

`frontend/src/main.tsx` güncellendi:
```tsx
<AuthProvider>
  <BrowserRouter>
    <App />
  </BrowserRouter>
</AuthProvider>
```
AuthProvider en dışta, BrowserRouter içinde — tüm bileşenler `useAuth()` erişebilir.

---

### Adım 6 — Backend Auth Middleware

`backend/auth.py` oluşturuldu:
- Firebase Admin SDK ile token doğrulama
- `verify_firebase_token()` dependency fonksiyonu
- Request header'dan `Authorization: Bearer <token>` alınır
- Token geçersizse 401 Unauthorized döner

Backend route'ları (`query.py`, `upload.py`, `fetch_data.py`, `fetch_news.py`, `compare.py`) güncellendi:
- Her endpoint'e `Depends(verify_firebase_token)` eklendi
- Giriş yapmamış kullanıcılar API'ye erişemez

---

### Adım 7 — Frontend API Client Token Gönderimi

`frontend/src/api/client.ts` güncellendi:
- Her API çağrısında Firebase `currentUser.getIdToken()` alınır
- `Authorization: Bearer <token>` header'ı eklenir
- Token yoksa (giriş yapılmamışsa) istek gönderilmez

---

### Çözülen Sorunlar

| Sorun | Çözüm |
|---|---|
| Firebase popup CORS hatası | Firebase Console'da authorized domains'e localhost eklendi |
| `onAuthStateChanged` ilk yüklemede null döner | `loading` state ile spinner gösterilir, auth resolve olunca kaldırılır |
| Backend'e token gönderilmiyordu | `client.ts`'te `getIdToken()` ile her isteğe Bearer token eklendi |

---

### Faz 5 / Gün 1 Çıktıları

- ✅ Firebase Authentication kuruldu (Google OAuth popup)
- ✅ AuthContext + AuthProvider pattern çalışıyor
- ✅ App.tsx auth guard: giriş yapmayanlar LoginPage görüyor
- ✅ Backend token doğrulama çalışıyor (401 Unauthorized)
- ✅ Frontend API client token gönderiyor
- ✅ TypeScript build hatasız (`npx tsc --noEmit`)

---

## 2026-07-24 — Cuma
**Faz: Faz 5 / Gün 2 — Landing Page Tam Ekran Yeniden Tasarım → FAZ 5 TAMAMLANDI ✅**

Bu oturumda landing page (LoginPage.tsx) sıfırdan yeniden tasarlandı. Mevcut dar ve basit sayfa yerine, tam ekran kaplayan, 9 bölümlük, inline SVG mockup'larla desteklenmiş profesyonel bir SaaS landing page yazıldı.

---

### Adım 1 — Mevcut Sayfanın Analizi

Eski `LoginPage.tsx` incelendi:
- `max-w-6xl` ile dar layout
- Basit hero (tek sütun, merkez hizalı)
- Trust strip (sadece 3 metin)
- 6 feature kartı (küçük, detaysız)
- Kısa CTA ve minimal footer
- Toplam ~190 satır

**Karar:** Sayfa tamamen silinip sıfırdan yazılacak. 9 bölüm, inline SVG mockup'lar, FAQ accordion, detaylı footer.

---

### Adım 2 — Hero Section (Tam Ekran, İki Sütun)

Yeni hero section tasarlandı:
- `min-h-screen` — tam ekran kaplaması
- `lg:grid-cols-2` — sol: metin, sağ: mockup
- Sol taraf: yeşil badge (animate-pulse), büyük başlık (gradient text: "Yapay Zeka"), açıklama, 2 CTA butonu
- Sağ taraf: `HeroChatMockup` inline SVG bileşeni
- Dekoratif gradient bloblar: 3 adet CSS circle (blue, purple, indigo), `blur-3xl`, `opacity-20`
- Mobilde tek sütun, mockup altta

---

### Adım 3 — Inline SVG Chat Mockup

`HeroChatMockup` bileşeni oluşturuldu (inline SVG, harici imaj yok):
- Koyu arka plan (`#1a1a2e`) üzerinde chat UI
- Title bar: kırmızı/sarı/yeşil dots (macOS tarzı)
- Kullanıcı mesajı: mavi balon — "THYAO'nun son çeyrek gelir tablosunu analiz eder misin?"
- AI yanıtı: koyu balon + mor avatar — "THYAO 2024 Q4 Gelir Tablosu: Hasılat, Net Kar, FAVÖK Marjı"
- Kullanıcı ikinci mesajı: "Peki PGSUS ile karşılaştır"
- Typing indicator: 3 nokta animasyonu (`<animate>` SVG elementi)
- SVG `viewBox="0 0 420 340"` — responsive scaling

---

### Adım 4 — Trust Strip ve Nasıl Çalışır

**Trust Strip:**
- `bg-gray-50` şerit
- 4 metrik, her biri ikon + text: "500+ Hisse" (BarChart3), "RAG Motoru" (BrainCircuit), "Gerçek Zamanlı" (Zap), "Türkçe AI" (Globe)
- `grid-cols-2 md:grid-cols-4` responsive grid

**Nasıl Çalışır? (3 Adım):**
- Numaralı daireler (01, 02, 03) içinde lucide-react ikonları (LogIn, Search, Sparkles)
- Her adım: numara + ikon + başlık + açıklama
- Adımlar arası `border-t-2 border-dashed border-gray-200` bağlantı çizgisi (sadece desktop)
- `md:grid-cols-3` responsive grid

---

### Adım 5 — Özellikler Kartları (6 Renkli Kart)

6 feature kartı yeniden tasarlandı:
- Her kart renkli daire ikon arka planıyla: `bg-blue-100`, `bg-green-100`, `bg-purple-100`, `bg-amber-100`, `bg-rose-100`, `bg-indigo-100`
- Daha büyük padding (`p-8`)
- Daha detaylı açıklamalar (2-3 cümle)
- `bg-gray-50` bölüm arka planı
- `lg:grid-cols-3 md:grid-cols-2` responsive grid
- `hover:shadow-lg transition-shadow duration-300` efekti

---

### Adım 6 — Platform Önizleme (App Preview)

İki sütun layout:
- Sol: "Platformu keşfedin" başlık + açıklama + 4 bullet point (CheckCircle2 ikonu) + CTA butonu
- Sağ: `AppPreviewMockup` inline SVG — browser frame (macOS dots + URL bar) + sidebar (Chat/Karşılaştır) + chat mesajları + input bar
- SVG `viewBox="0 0 480 320"` — responsive
- `shadow-xl` ve `border border-gray-100` ile derinlik efekti

---

### Adım 7 — FAQ Accordion

5 soru-cevap çifti, `useState<number | null>` ile toggle:
- "agentick.io nedir?"
- "Hangi verilere erişebilirim?"
- "Ücretsiz mi?"
- "Verilerim güvende mi?"
- "RAG teknolojisi ne anlama geliyor?"

Her soru bir kart:
- Tıklanınca `openFaq` state güncellenir (aynı soruya tıklanırsa kapanır)
- `ChevronDown` ikonu açıkken `rotate-180` animasyonu
- İçerik `max-h-0` / `max-h-60` transition ile açılır/kapanır
- `bg-white rounded-xl border border-gray-100` kart stili

---

### Adım 8 — Final CTA ve Footer

**Final CTA:**
- `bg-gray-900` tam genişlik koyu banner
- Büyük beyaz başlık: "Yapay zeka destekli analize hemen başlayın"
- Gri açıklama + beyaz CTA butonu (hover'da `bg-gray-100`)

**Footer:**
- 3 sütun grid: Logo + açıklama | Ürün linkleri (scroll-to) | İletişim (Mail ikonu)
- Alt bar: `border-t border-gray-100`, © 2026 + "Istanbul, Türkiye"

---

### Adım 9 — TypeScript Doğrulama

`npx tsc --noEmit` çalıştırıldı — hatasız geçti. Tüm lucide-react ikonları doğru import edilmiş, tüm prop'lar tipli.

---

### Çözülen Sorunlar

| Sorun | Çözüm |
|---|---|
| SVG içinde Türkçe karakterler (ş, ç, ı, ü) render sorunu | `fontFamily="Inter, sans-serif"` ile UTF-8 desteği sağlandı |
| FAQ accordion birden fazla soru aynı anda açılıyordu | `useState<number \| null>` ile tek soru açık kalacak şekilde toggle |
| Dekoratif bloblar tıklamayı engelliyordu | `pointer-events-none` eklendi |
| Hero mockup mobilde çok büyük | `w-full h-auto` SVG + responsive grid ile otomatik küçülme |

---

### Faz 5 Çıktı Kriterleri ✅

- ✅ Firebase Auth çalışıyor (Google OAuth popup)
- ✅ Auth guard: giriş yapmayanlar landing page görüyor
- ✅ Landing page 9 bölüm, tam ekran, beyaz arka plan
- ✅ Hero SVG chat mockup düzgün render
- ✅ FAQ accordion aç/kapa çalışıyor
- ✅ Tüm butonlar Google OAuth popup açıyor
- ✅ Mobil/tablet/desktop responsive
- ✅ TypeScript hatasız (`npx tsc --noEmit`)
- ✅ Backend auth middleware çalışıyor

---

### Sıradaki — Faz 6

- [ ] Deployment (Railway + Vercel)
- [ ] Custom domain (agentick.io)
- [ ] Production environment variables

---

## 2026-07-24 — Cuma
**Faz: Faz 6 — Portföy Analiz Dashboard'u + Bedelsiz Sermaye Artırımı Verisi**

Bu oturumda portföy analiz dashboard'u sıfırdan tasarlanıp uygulandı. Kullanıcı BIST hisselerinden oluşan bir portföy sepeti oluşturup AI destekli analiz yapabiliyor. Ayrıca bedelsiz sermaye artırımı (stock splits) verisi sisteme eklendi.

---

### Adım 1 — Firebase Firestore Kurulumu

- `frontend/src/config/firebase.ts` → `getFirestore` import, `db` export
- `frontend/src/services/portfolioService.ts` oluşturuldu:
  - Firestore CRUD: `getPortfolio`, `addHolding`, `updateHolding`, `removeHolding`
  - Collection yapısı: `users/{uid}/portfolios/default`
  - Holding yapısı: `{ ticker, shares, avgCost, addedAt }`

---

### Adım 2 — Backend: Sektör Verisi ve Bedelsiz Sermaye Artırımı

**`src/ingestion/bist_finance_client.py` güncellendi:**
- `ratios` tablosuna `sector` kolonu eklendi (ALTER TABLE + try/except)
- `fetch_and_store()` içinde `info.get("sector")` değeri ratios satırına yazılıyor
- `stock_splits` tablosu oluşturuldu: `ticker`, `split_date`, `ratio`
- `yf_ticker.splits` verisi çekilip kaydediliyor (tüm BIST hisseleri için otomatik)

**Test:** SASA için 11 bedelsiz işlem başarıyla kaydedildi (2003-2024 arası).

---

### Adım 3 — Backend: Metrics Helper Refactor

**`backend/services/metrics_utils.py` oluşturuldu:**
- `compare.py`'den `get_conn`, `fetch_latest_ratios`, `fetch_latest_income`, `fetch_latest_balance`, `fetch_dividend_yield`, `build_ticker_metrics` fonksiyonları taşındı
- `fetch_dividends()` eklendi (son 2 yıllık temettü verisi)
- `build_ticker_metrics()`'e `sector` alanı eklendi
- `compare.py` bu modülden import edecek şekilde güncellendi

---

### Adım 4 — Backend: Portföy Endpoint'leri

**`backend/routes/portfolio.py` oluşturuldu — 3 endpoint:**

**POST `/api/portfolio/metrics`:**
- Her ticker için `fetch_and_store()` (asyncio.gather)
- Per-holding: currentPrice, marketValue, costBasis, profitLoss, profitLossPct, weight, sector
- Summary: totalValue, totalCost, totalProfitLoss, weightedPE, weightedDividendYield, weightedNetMargin
- Sektör dağılımı: `[{sector, weight, tickers}]`
- Konsantrasyon uyarıları: tek hisse >%30, tek sektör >%40
- Temettü takvimi: son 2 yıllık temettü ödemeleri

**POST `/api/portfolio/ask`:**
- `run_agent()` çağrısı, min ticker kısıtlaması 1'e düşürüldü
- Tek ticker ise normal agent, çoklu ise multi-ticker agent

**POST `/api/portfolio/news`:**
- Her ticker için `search_news()` çağrısı (ticker tag + şirket adı fallback)
- Deduplicate (link bazlı), tarihe göre sırala
- Alakasız genel haber göstermez — sadece şirketle ilgili haberler

`backend/main.py`'ye `portfolio_router` kaydedildi.

---

### Adım 5 — Frontend: API Client Genişletmesi

**`frontend/src/api/client.ts`'e eklendi:**
- 7 yeni interface: `PortfolioHoldingInput`, `PortfolioHoldingMetrics`, `PortfolioSummary`, `SectorAllocation`, `DividendEntry`, `PortfolioMetricsResult`, `NewsArticle`
- 3 yeni fonksiyon: `fetchPortfolioMetrics()`, `askPortfolioQuestion()`, `fetchPortfolioNews()`

---

### Adım 6 — Frontend: 8 Portföy Dashboard Bileşeni

**`PortfolioManager.tsx`** — Holding CRUD:
- Ticker dropdown (BIST_TICKERS, kullanılmış olanlar hariç) + shares input + avgCost input
- Her satır: ticker badge + lot + maliyet + toplam + sil butonu
- "Hisse Ekle" formu toggle

**`PortfolioSummaryCards.tsx`** — 6 özet kart (3×2 grid):
- Toplam Değer (Banknote ikonu), Toplam Maliyet (Target), K/Z (TrendingUp/Down)
- K/Z Oranı (Percent), Ağırlıklı F/K (BarChart3), Ağırlıklı Temettü (Coins)
- Yeşil/kırmızı renk kodlaması (kâr/zarar), skeleton loading

**`SectorChart.tsx`** — CSS bar chart:
- Her sektör: renkli nokta + isim + ticker'lar + yüzde + animasyonlu bar
- 8 farklı renk paleti, maxWeight'e göre orantılı genişlik

**`ConcentrationWarnings.tsx`** — Amber uyarı kartları:
- AlertTriangle ikonu, uyarı yoksa render etmez

**`PortfolioHoldingsTable.tsx`** — 9 kolonlu tablo:
- Hisse, Lot, Maliyet, Fiyat, Değer, K/Z, K/Z%, Ağırlık, Sektör
- Yeşil/kırmızı font renkleri, sektör badge

**`DividendCalendar.tsx`** — Temettü timeline:
- Türkçe tarih formatı ("2 Eylül 2025"), ticker badge, tutar + "/hisse" etiketi
- Veri yoksa "Temettü verisi bulunamadı" mesajı

**`PortfolioNews.tsx`** — Haber kartları:
- Mount'ta `fetchPortfolioNews(tickers)` çağrısı
- Kaynak badge + başlık + özet + tarih + ticker badge + link ikonu
- Loading skeleton, error handling

**`PortfolioChat.tsx`** — AI soru-cevap:
- ComparisonChat klonu, `askPortfolioQuestion` çağrısı
- Ticker değişince chat sıfırlanır
- Max 5 ticker badge gösterilir, fazlası "+N"

---

### Adım 7 — Frontend: Sayfa ve Navigasyon

**`frontend/src/pages/PortfolioPage.tsx` oluşturuldu:**
- Dashboard layout: Portföy Sepeti → "Portföyü Analiz Et" butonu → Özet Kartlar → Uyarılar → (Sektör + Temettü) 2 kolon → Holdings Tablosu → (Haberler + Chat) 2 kolon
- Mount'ta Firestore'dan portföy yükle, değişiklikleri Firestore'a kaydet
- Empty state: Logo + açıklama

**`frontend/src/App.tsx`** — `<Route path="/portfolio" element={<PortfolioPage />} />` eklendi

**`frontend/src/components/Sidebar.tsx`** — NAV_ITEMS'a `{ label: 'Portföy', path: '/portfolio', icon: Briefcase }` eklendi

---

### Adım 8 — SQL Retriever: Bedelsiz Desteği

**`src/retrievers/sql_retriever.py` güncellendi:**
- `DB_SCHEMA`'ya `stock_splits` tablosu tanımı eklendi (ticker, split_date, ratio)
- `all_tables` listesine `stock_splits` eklendi
- Agent artık "bedelsiz sermaye artırımı" sorularını SQL'e çevirebilir

---

### Adım 9 — Hata Düzeltmeleri

| Sorun | Çözüm |
|---|---|
| Backend 500 Internal Server Error (tüm endpoint'ler) | `FIREBASE_PRIVATE_KEY` boş — `auth.py`'ye dev mode bypass eklendi |
| Portföy haberleri tüm Bloomberg haberlerini getiriyordu | `search_news` keyword araması OR → AND'e çevrildi |
| Haber fallback'i ilgisiz genel haberleri gösteriyordu | Genel haber fallback kaldırıldı, sadece ilgili haberler |
| Temettü tarihleri ham ISO format (2025-09-02) | Türkçe format: "2 Eylül 2025" + "/hisse" etiketi |
| Dashboard'ta $ (dolar) ikonu vardı | `DollarSign` → `Banknote` (toplam değer) ve `Coins` (temettü) |

---

### Faz 6 Çıktı Kriterleri ✅

- ✅ Portföy sepeti: hisse ekleme/çıkarma (Firestore'da kalıcı)
- ✅ Özet kartlar: toplam değer, maliyet, K/Z, ağırlıklı F/K ve temettü
- ✅ Sektör dağılımı bar chart
- ✅ Konsantrasyon uyarıları (tek hisse >%30, tek sektör >%40)
- ✅ Holdings detay tablosu (9 kolon, yeşil/kırmızı renk kodlaması)
- ✅ Temettü takvimi (Türkçe tarih, hisse başı tutar)
- ✅ Portföy haberleri (sadece ilgili haberler)
- ✅ AI portföy asistanı (serbest soru-cevap)
- ✅ Bedelsiz sermaye artırımı verisi (tüm hisseler için otomatik)
- ✅ Sidebar'da Portföy sekmesi
- ✅ TypeScript hatasız (`npx tsc --noEmit`)

---

### Sıradaki — Faz 7

- [ ] Deployment (Railway + Vercel)
- [ ] Custom domain (agentick.io)
- [ ] Production environment variables

---

## 2026-07-27 — Pazartesi
**Sprint 1 — Güvenlik Sertleştirme (Kritik Öncelik)**

Kapsamlı proje denetimi sonrası tespit edilen güvenlik ve stabilite sorunları çözüldü.

---

### Adım 1 — API Key Temizliği ve Git Geçmişi

**Sorun:** `.env` ve `frontend/.env` dosyaları git geçmişinde commit edilmişti. API key'ler (Anthropic, LangChain, Qdrant) geçmişten erişilebilir durumdaydı.

**Çözüm:**
- `git filter-repo --invert-paths --path .env --path frontend/.env --force` ile geçmişten silindi
- `.gitignore`'a `frontend/.env`, `.env.local`, `.env.*.local`, `frontend/.env.local` eklendi
- `.env.example` (backend) ve `frontend/.env.example` (frontend) şablonları oluşturuldu
- Tüm API key'ler rotate edildi (Anthropic, LangChain, Qdrant — eski key'ler silindi)
- `git push --force -u origin main` ile remote temizlendi
- `git show origin/main:.env` → "fatal: path '.env' exists on disk, but not in 'origin/main'" ✅

---

### Adım 2 — Firebase Auth Production-Safe

**Sorun:** `backend/auth.py` production'da `FIREBASE_PRIVATE_KEY` olmadan sessizce dev mode'a düşüyordu. Hata mesajında internal exception detayları sızıyordu.

**Çözüm:**
- `ENVIRONMENT` env var kontrolü eklendi
- Production'da `FIREBASE_PRIVATE_KEY` yoksa `RuntimeError("FIREBASE_PRIVATE_KEY is required in production.")` fırlatılır
- `_is_dev_mode` explicit flag ile kontrol
- Hata mesajından exception detayları çıkarıldı (sadece "Token doğrulama başarısız")
- `logging` modülüne geçildi (`logger.warning`, `logger.error`)

---

### Adım 3 — Qdrant Vector Retriever Hata Toleransı

**Sorun:** Qdrant Cloud bağlantı hatalarında `vector_retriever.py` crash ediyordu. `os.environ["QDRANT_URL"]` KeyError fırlatabiliyordu. Her `search()` çağrısında yeni client oluşturuluyordu.

**Çözüm:**
- Singleton `QdrantClient` + singleton `SentenceTransformer` (thread-safe, `threading.Lock()`)
- `os.environ.get()` ile KeyError önleme
- Tüm `search()` fonksiyonu try/except ile sarıldı — Qdrant hatalarında boş liste döner
- Payload erişimi `.get()` ile (defaults ile güvenli erişim)

---

### Adım 4 — API Endpoint Timeout'ları

**Sorun:** Agent çağrıları veya yfinance fetch takılırsa istek sonsuza kadar bekleyebiliyordu. Validation hataları `return {"error": ...}` ile dönerken HTTP status kodu 200 oluyordu.

**Çözüm:**
- `backend/routes/query.py`: `asyncio.wait_for(timeout=120)` (AGENT_TIMEOUT)
- `backend/routes/fetch_data.py`: `asyncio.wait_for(timeout=60)` (FETCH_TIMEOUT)
- `backend/routes/compare.py`: yfinance fetch 60s, agent 120s timeout
- `backend/routes/portfolio.py`: yfinance fetch 60s, agent 120s timeout
- Tüm validation hataları `HTTPException(status_code=400/422)` ile döner
- `TimeoutError` → 504 Gateway Timeout, `Exception` → 500 Internal Server Error

---

### Adım 5 — DB Bağlantı Leak Önleme

**Sorun:** `compare.py` ve `portfolio.py`'de SQLite bağlantıları exception durumunda kapatılmıyordu.

**Çözüm:**
- Tüm SQLite bağlantıları `try/finally: conn.close()` pattern'i ile sarıldı
- Exception olsa bile bağlantı her zaman kapatılır

---

### Sprint 1 Çıktı Kriterleri ✅

- ✅ Git geçmişinden API key'ler temizlendi
- ✅ Tüm API key'ler rotate edildi (eski key'ler silindi)
- ✅ Firebase Auth production'da güvenli
- ✅ Qdrant hatalarında crash olmuyor (boş liste döner)
- ✅ Tüm endpoint'lerde timeout var
- ✅ DB bağlantı leak'leri kapatıldı
- ✅ `.env.example` şablonları oluşturuldu

---

## 2026-07-27 — Pazartesi
**Sprint 2 — Test Altyapısı, CI/CD, Logging, Input Validation**

Sprint 1'deki güvenlik düzeltmeleri sonrası kalite ve sürdürülebilirlik altyapısı kuruldu.

---

### Adım 1 — Test Altyapısı (pytest)

**Yapılanlar:**
- `pyproject.toml`'a dev bağımlılıkları eklendi: `pytest>=8.0`, `pytest-asyncio>=0.24`, `httpx>=0.28`
- `[tool.pytest.ini_options]` ile `asyncio_mode = "auto"` ve `testpaths = ["tests"]` ayarlandı
- `tests/conftest.py` oluşturuldu: `TestClient` fixture + dev auth bypass header

**Test dosyaları:**
- `tests/test_health.py` — Health endpoint: 200 status, `status=ok`, `version` alanı
- `tests/test_auth.py` — Dev mode mock user (`uid=dev-user`, `email=dev@localhost`) + production mode `RuntimeError`
- `tests/test_validation.py` — 12 input validation testi:
  - Boş soru → 400, eksik soru → 422
  - Boş ticker → 400
  - Tek ticker karşılaştırma → 400, 6+ ticker → 400
  - Boş portföy holdings → 400, boş portföy sorusu → 400
  - Portföy ticker'sız → 400, portföy haberleri ticker'sız → 400
  - Geçersiz ticker upload → 400 ("Geçersiz ticker" mesajı)
  - PDF olmayan dosya upload → 400

**Sonuç:** `uv run pytest tests/ -v` → 14 test, tümü geçiyor ✅

---

### Adım 2 — GitHub Actions CI/CD Pipeline

**`.github/workflows/ci.yml` oluşturuldu:**

**Tetikleyici:** Push veya PR → `main` branch

**Job 1 — test (Backend):**
1. `actions/checkout@v4`
2. `astral-sh/setup-uv@v4` ile uv kurulumu
3. `uv python install 3.12`
4. `uv sync --extra dev`
5. `uv run pytest tests/ -v` (ENVIRONMENT=development, test API key'leri ile)

**Job 2 — frontend-build (Frontend):**
1. `actions/setup-node@v4` (Node.js 20, npm cache)
2. `npm ci` (frontend/)
3. `npx tsc --noEmit` (TypeScript tip kontrolü)
4. `npm run build` (Vite production build, test Firebase config ile)

---

### Adım 3 — print() → logging Migrasyonu

**Değiştirilen dosyalar:**
- `backend/main.py` — `logging.basicConfig()` merkezi config eklendi
- `backend/routes/query.py` — logger
- `backend/routes/fetch_data.py` — logger
- `backend/routes/compare.py` — logger
- `backend/routes/portfolio.py` — logger
- `backend/routes/upload.py` — logger
- `backend/services/pdf_pipeline.py` — logger
- `src/agent/router_node.py` — 3 print → logger
- `src/retrievers/sql_retriever.py` — print → logger.debug
- `src/retrievers/news_retriever.py` — print → logger.info
- `src/ingestion/bist_finance_client.py` — ~15 print → logger
- `src/ingestion/news_client.py` — print → logger (kütüphane kodu)
- `src/ingestion/build_vector_index.py` — print → logger + os.environ.get()
- `src/ingestion/pdf_chunker.py` — print → logger (kütüphane kodu)

**Kalan:** `src/cli_test.py`'de 6 print — standalone CLI aracı, düşük öncelik.

---

### Adım 4 — Input Validation Güçlendirme

**`backend/routes/upload.py` yeniden yazıldı:**
- `VALID_TICKERS` set (30 BIST-30 hissesi) — whitelist validation
- `MAX_FILE_SIZE = 50 * 1024 * 1024` (50 MB limit)
- `SAFE_FILENAME_RE = re.compile(r"^[\w\-. ]+$")` — path injection önleme
- `_validate_ticker()` ve `_validate_file()` helper fonksiyonları
- Dosya içeriği okunup boyut kontrolü yapılır
- Tüm hatalar `HTTPException(status_code=400)` ile döner

**Diğer endpoint'ler:**
- Tüm `return {"error": ...}` ifadeleri `HTTPException` ile değiştirildi
- Karşılaştırma: min 2, max 5 ticker validasyonu
- Portföy: boş holdings, boş soru, boş tickers validasyonu
- Named constants: `HOLDING_CONCENTRATION_THRESHOLD = 30`, `SECTOR_CONCENTRATION_THRESHOLD = 40`

---

### Sprint 2 Çıktı Kriterleri ✅

- ✅ 14 pytest testi — tümü geçiyor
- ✅ GitHub Actions CI/CD — her push/PR'da otomatik test + build
- ✅ Tüm kütüphane kodu print → logging'e migrate edildi
- ✅ Ticker whitelist (30 BIST-30)
- ✅ 50MB dosya boyutu limiti
- ✅ Güvenli dosya adı regex
- ✅ Tüm endpoint'lerde HTTPException ile doğru HTTP status kodları

---

### Dokümantasyon Güncellemesi

- `dokuman.md` güncellendi: Sprint 1 + Sprint 2 çalışmaları eklendi, teknoloji stack'e test/CI/CD/logging eklendi, klasör yapısı güncellendi
- `mimari.md` güncellendi: Güvenlik katmanları, test altyapısı, CI/CD bölümleri eklendi, implementation durumu tablosu güncellendi
- `daily_log.md` güncellendi (bu kayıt)
- `README.md` yeniden yazıldı: UI ekran görüntüsü, badge'ler, güvenlik/kalite bölümü, güncel proje yapısı

---

### Sıradaki

- [ ] Deployment (Railway + Vercel)
- [ ] Custom domain (agentick.io)
- [ ] Rate limiting
- [ ] Otomatik Screening/Alert

---

## 2026-07-28 — Salı
**Sprint 3 / Gün 1 — Kapsamlı Denetim + Backend Güvenlik Düzeltmeleri**

Projenin tamamı (89 dosya, ~6.200 satır kod + 4 doküman) baştan sona okundu.
Kod ile doküman arasındaki uyuşmazlıklar ve gerçek bug'lar çıkarıldı; bu gün
backend tarafındaki güvenlik ve veri bütünlüğü sorunları giderildi.

**Denetimde çıkan tablo:** 6 doküman-kod uyuşmazlığı + 8 gerçek risk.
Bunlardan üçü kritikti: Qdrant'ta sessiz veri kaybı, auth'un fail-open olması ve
LLM'in ürettiği SQL'in doğrudan çalıştırılması.

---

### Adım 1 — Qdrant Point ID Çakışması (veri kaybı)

**Sorun:** `build_vector_index.upload_to_qdrant()` point ID olarak `0, 1, 2, ...`
sıra numarası kullanıyordu. THYAO yüklenip ardından TUPRS yüklendiğinde aynı ID'ler
üretiliyor ve THYAO'nun chunk'ları **sessizce üzerine yazılıyordu**. Yani ikinci
PDF'ten sonra ilk şirketin vektör verisi kayboluyordu.

**Çözüm:**
- `uuid.uuid5(POINT_NAMESPACE, f"{ticker}|{source_file}|{chunk_index}")` ile
  deterministik, çakışmayan ID üretimi
- `chunk_index` payload'a eklendi (mimari.md'de yazıyordu ama kodda yoktu)
- `delete_existing_chunks()`: aynı dosya yeniden yüklenirse eski chunk'lar
  ticker + source_file filtresiyle silinir (kısalan raporda artık kalıntı kalmaz)
- `source_file` için keyword payload index eklendi (filtreli silme için)
- Doğrulama: `_point_id('THYAO','a.pdf',0)` ve `_point_id('TUPRS','a.pdf',0)`
  farklı UUID üretiyor ✅

---

### Adım 2 — Auth Fail-Open

**Sorun:** `os.getenv("ENVIRONMENT", "development")` — ortam değişkeni tanımsızsa
dev mode'a düşüyor ve **tüm token'lar kabul ediliyordu**. Projenin `.env` dosyasında
`ENVIRONMENT` hiç tanımlı değildi; bu haliyle deploy edilse API tamamen açık olurdu.

**Çözüm:**
- Varsayılan `production` yapıldı (fail-safe)
- Dev bypass yalnızca `development / dev / local / test` değerlerinde açılır;
  `staging`, `prod`, `canary` gibi bilinmeyen adlar production gibi davranır
- `init_auth()` FastAPI lifespan'inde çağrılıyor → yanlış yapılandırmada servis
  hiç ayağa kalkmıyor (her istekte 500 yerine)
- `load_dotenv()` auth ve main modüllerine eklendi (import sırasına bağımlılık kalktı)
- `.env` dosyasına `ENVIRONMENT=development` eklendi (yerel geliştirme bozulmasın)

---

### Adım 3 — Text-to-SQL Güvenliği

**Sorun:** `_run_sql()` LLM'in ürettiği SQL'i doğrudan `conn.execute()` ile
çalıştırıyordu. Yüklenen PDF içeriği veya kullanıcı sorusu üzerinden prompt
injection ile `DELETE FROM ratios` gibi bir sorgu üretilmesi mümkündü.

**Çözüm:**
- `_validate_sql()`: yalnızca tek bir `SELECT`/`WITH`; `;`, `--`, `/* */` ve
  `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/REPLACE/TRUNCATE/ATTACH/PRAGMA/VACUUM`
  içeren sorgular reddedilir
- Bağlantı salt-okunur açılıyor: `sqlite3.connect("file:...?mode=ro", uri=True)` —
  guard atlansa bile yazma imkânsız
- `DB_SCHEMA`'ya `ratios.sector` kolonu eklendi (DB'de vardı ama LLM'e gösterilmiyordu,
  bu yüzden agent sektör sorularını SQL'e çeviremiyordu)

---

### Adım 4 — CORS, Ticker Whitelist ve Rate Limiting

**Sorun:** CORS sadece localhost'a izin veriyordu (deployment blocker); ticker
whitelist'i yalnızca upload endpoint'inde vardı; hiçbir kota yoktu — her `/api/ask`
4+ LLM çağrısı tetikliyor.

**Çözüm:**
- `backend/constants.py` oluşturuldu: `VALID_TICKERS` + `validate_ticker()` +
  `validate_tickers()`. Tek kaynak; ask, fetch-data, compare/metrics, compare/ask,
  portfolio/metrics, portfolio/ask, portfolio/news, news/search uçlarının hepsinde uygulanıyor
- `backend/rate_limit.py` oluşturuldu: kullanıcı (uid) başına kayan pencere,
  dakika + gün limiti, aşımda 429 + `Retry-After`, bellek sızıntısına karşı periyodik sweep
- `backend/main.py`: CORS listesi `CORS_ORIGINS` env'inden okunuyor, `"*"` reddediliyor;
  kullanılmayan `StaticFiles`/`Path` import'ları temizlendi; sürüm 0.4.0

---

### Adım 5 — Haber Aramasında Genel Fallback

**Sorun:** `news_retriever.search()` ticker filtresi boş dönünce **filtresiz genel
arama** yapıyordu; şirketle ilgisi olmayan haberler synthesizer'a gidiyordu.

**Çözüm:** `news_client.search_news_for_ticker()` ortak helper'ı yazıldı:
ticker etiketi → şirket anahtar kelimeleri (`KNOWN_TICKERS`) sırası, genel arama yok.
`news_retriever`, `/api/portfolio/news` ve `/api/news/search` aynı helper'ı kullanıyor
(portfolio.py'deki kopya mantık kaldırıldı).

---

### Adım 6 — Dosya Adı Doğrulaması

**Sorun:** `^[a-zA-Z0-9_\-\.]+$` regex'i boşluklu ve Türkçe karakterli dosya adlarını
reddediyordu (KAP raporları genelde böyle). Path traversal koruması da regex'e bağlıydı.

**Çözüm:** `_safe_filename()`:
- `Path(name).name` ile dizin bileşenleri atılır → traversal etkisiz
- `..` içeren adlar reddedilir
- `^[\w\-. ()]+$` (Unicode `\w` Türkçe harfleri kapsar)
- `.pdf` uzantısı + `%PDF` magic byte kontrolü, 200 karakter ad sınırı, boş dosya reddi

---

### Gün 1 Çıktıları

- ✅ Qdrant veri kaybı bug'ı kapatıldı (deterministik uuid5 point ID)
- ✅ Auth fail-safe: `ENVIRONMENT` tanımsızsa production, startup'ta doğrulama
- ✅ Text-to-SQL guard + salt-okunur DB bağlantısı
- ✅ CORS env'den yönetiliyor, rate limiting devrede
- ✅ Ticker whitelist tüm uçlarda (`backend/constants.py` tek kaynak)
- ✅ Haber aramasında filtresiz genel fallback kaldırıldı
- ✅ Dosya adı doğrulaması: traversal etkisiz, Türkçe/boşluklu adlar kabul

**Yarına kalan:** frontend bug'ları (portföy metrik tazeleme, sohbet hafızası).

---

## 2026-07-29 — Çarşamba
**Sprint 3 / Gün 2 — Frontend Düzeltmeleri**

Gün 1'de backend tarafı kapatıldı. Bugün frontend'de kalan iki bug giderildi:
portföy metriklerinin lot/maliyet değişiminde tazelenmemesi ve hiç bağlanmamış
sohbet hafızası.

---

### Adım 1 — Portföy Metrikleri Tazelenmiyordu

**Sorun:** `PortfolioPage` useEffect bağımlılığı `[holdings.length]` idi; lot veya
maliyet düzenlendiğinde (eleman sayısı değişmediği için) metrikler eski kalıyordu.

**Çözüm:** İçeriğe duyarlı `holdingsKey` (`ticker:shares:avgCost` birleşimi) bağımlılığı.

---

### Adım 2 — Sohbet Hafızası Geri Bağlandı

**Sorun:** `conversationStorage.ts` (90 satır) yazılmıştı ama **hiçbir yerden import
edilmiyordu**. Faz 4'teki sayfa ayrımında Sidebar'ın konuşma listesi düşmüş; sohbetler
sadece bellekte tutuluyor, sayfa yenilenince kayboluyordu — oysa dokümanlar kalıcı
hafızayı özellik olarak sayıyordu.

**Çözüm:**
- `App.tsx`: `conversations` + `activeId` state'i, localStorage senkronu
  (`upsert`/`getAll`/`remove`), ticker değişiminde konuşma güncellemesi
- `Sidebar.tsx`: "Yeni Sohbet" butonu + tarih grupli konuşma listesi
  (Bugün / Dün / Bu Hafta / Daha Önce), ticker rozeti, hover'da silme
- Agent yanıtı, sorunun sorulduğu konuşma nesnesine yazılıyor — kullanıcı yanıt
  beklerken başka sohbete geçse bile cevap doğru yere düşüyor

---

### Gün 2 Çıktıları

- ✅ Portföy metrikleri lot/maliyet düzenlemesinde de tazeleniyor
- ✅ Sohbet hafızası kalıcı: konuşmalar localStorage'da, Sidebar'da tarih grupli liste
- ✅ Yeni sohbet başlatma ve konuşma silme çalışıyor
- ✅ `npx tsc --noEmit` hatasız

**Yarına kalan:** test paketinin genişletilmesi ve dört dokümanın koda göre
güncellenmesi (özellikle sentez modeli uyuşmazlığı).

---

## 2026-07-30 — Perşembe
**Sprint 3 / Gün 3 — Test Paketi ve Dokümantasyon**

Kod tarafı iki günde kapandı. Bugün regresyon güvencesi için test paketi
14'ten 73'e çıkarıldı ve dört doküman kodla birebir uyumlu hale getirildi.

---

### Adım 1 — Model Uyuşmazlığı (doküman ↔ kod)

`synthesizer_node.py` Claude Haiku 4.5 kullanıyordu; README, mimari.md ve dokuman.md
"Claude Sonnet 4.6" diyordu. Maliyet tercihi bilinçli olduğu için **dokümanlar koda
göre düzeltildi**. Ayrıca haber cache süresi (30 gün → 1 saat TTL / 7 gün saklama) ve
RSS kaynağı (tek kaynak: Bloomberg HT) gerçek değerlerle güncellendi.

---

### Adım 2 — Testler

**Yeni test dosyaları:**
- `tests/test_sql_guard.py` — SELECT/WITH kabul, DDL/DML ve çoklu ifade reddi,
  reddedilen sorgunun DB'ye hiç gitmediği, bağlantının gerçekten salt-okunur olduğu
- `tests/test_rate_limit.py` — dakika/gün limiti, kullanıcı bazlı izolasyon,
  0 ile kapatma, 429 + Retry-After
- `tests/test_upload_security.py` — traversal etkisizleştirme, boşluk/Türkçe karakter
  kabulü, uzantı/uzunluk/shell karakteri reddi

**Genişletilenler:**
- `test_auth.py` — fail-safe davranışı (ENVIRONMENT tanımsız, bilinmeyen ortam adları)
- `test_validation.py` — tüm uçlarda BIST-30 dışı ticker reddi
- `conftest.py` — rate limit testlerde kapalı, her testten sonra state reset

**Sonuç:** `uv run pytest tests/ -q` → **73 test, tümü geçiyor** (önceki 14)
`npx tsc --noEmit` → hatasız, `npm run build` → başarılı

---

### Not: Test Beklentisi Düzeltmesi

`test_rejects_traversal` ilk yazılışında `../../etc/passwd.pdf` girdisinin hata
fırlatmasını bekliyordu. Kod bunu reddetmek yerine taban adı alıp `passwd.pdf`
döndürüyor — bu zaten doğru ve güvenli davranış (dosya `data/raw` dışına çıkamıyor).
Test, gerçek davranışı doğrulayacak şekilde `test_traversal_is_neutralised` olarak
yeniden yazıldı; `..` içeren adlar için ayrı bir red testi eklendi.

---

### Adım 3 — Dokümantasyon Güncellemesi

- `README.md`: badge'ler (Haiku 4.5, 73 test), mimari diyagramı, stack tablosu,
  güvenlik/kalite bölümü, proje yapısı, RSS kaynağı, sohbet hafızası açıklaması
- `mimari.md`: güvenlik katmanları (CORS → Auth → Rate Limit → Validation → Timeout →
  SQL Guard → DB Safety → Logging), Qdrant point ID stratejisi, haber arama sırası,
  App.tsx state modeli, Sidebar hiyerarşisi, test/CI bölümü, implementasyon durumu
- `dokuman.md`: Sprint 3 bulgu-çözüm tablosu, klasör yapısı, deployment öncesi
  zorunlu env ayarları, bilinen sınırlar
- `daily_log.md`: bu kayıt

---

### Sprint 3 Çıktı Kriterleri ✅

- ✅ Denetimde çıkan 10 sorunun tamamı giderildi
- ✅ 73 pytest testi, tümü geçiyor (önceki 14)
- ✅ `npx tsc --noEmit` hatasız, `npm run build` başarılı
- ✅ Dört doküman kodla birebir uyumlu hale getirildi

---

### Sıradaki

- [ ] Deployment (Railway + Vercel) — `ENVIRONMENT=production`, `FIREBASE_PRIVATE_KEY`,
      `CORS_ORIGINS` zorunlu
- [ ] Custom domain (agentick.io)
- [ ] Çok instance'lı deploy için rate limit sayaçlarını Redis'e taşıma
- [ ] Otomatik Screening/Alert

---

## 2026-07-31 — Cuma
**Kaynak Gösterimi — Cevap Hangi Dosyanın Hangi Sayfasından Geldi**

Agent bugüne kadar cevabın içine metin olarak alıntı yazıyordu (`citation`), ama
kullanıcı **hangi kaynağın gerçekten kullanıldığını** göremiyordu: 504 sayfalık bir
faaliyet raporunda cevabın 23. sayfadan mı 310. sayfadan mı geldiği belirsizdi.
Bu oturumda synthesizer'a verilen kaynaklar yapısal olarak dışarı taşındı ve her
mesajın altında açılabilir bir kaynak listesi olarak gösterildi.

---

### Adım 1 — Retriever'ların Kaynak Metadata'sı Zenginleştirildi

Üç retriever da artık kaynak tipini ve yerini açıkça döndürüyor:

- `vector_retriever.py`: `source_type: "vector"` ve `chunk_index` eklendi
  (dosya adı, sayfa, bölüm zaten vardı)
- `sql_retriever.py`: `pdf_tables` sorgusunda satırlardan **sayfa numaraları toplanıyor**,
  citation'a `(s.12, s.13)` olarak yazılıyor, `source_type` `"pdf"` oluyor.
  Finansal sorgularda ise `source_type: "sql"` + kullanılan `tables` + `period_range`
- `news_retriever.py`: `title`, `source`, `published_at` alanları eklendi

Böylece SQL retriever'ın tek `source_type: "sql"` etiketi ikiye ayrıldı — PDF tablosu
ile yfinance verisi UI'da farklı gösterilebiliyor.

---

### Adım 2 — Synthesizer: Kullanılan Kaynakların Ayrı Listesi

`synthesizer_node.py` içinde kaynak seçimi ile prompt kurgusu ayrıldı:

- `_select_sources()` — skora göre sıralayıp `MAX_SOURCES` (12) ile kırpar
- `_build_context()` — artık seçilmiş listeyi alıyor, kendi kırpmasını yapmıyor
- `_to_source()` — retriever çıktısını frontend'in anlayacağı sade kayda çevirir
  (tip, dosya, sayfalar, bölüm, tablo, skor, 240 karakterlik `snippet`)
- `build_source_list()` — dışarıdan test edilebilir giriş noktası

Kritik nokta: liste **modele gerçekten verilen** 12 kaynaktan üretiliyor, retriever'ın
bulduğu ham sonuçların tamamından değil. Kullanıcı, cevabı üreten alıntıları görüyor.

---

### Adım 3 — State ve API Zinciri

- `state.py`: `used_sources: list[dict]` alanı
- `graph.py`: initial state'e `used_sources: []`, dönüşte `sources` anahtarı
- `backend/routes/`: `query.py`, `compare.py`, `portfolio.py` — üçü de yanıta
  `sources` ekliyor
- `api/client.ts`: `AgentSource` tipi (`vector | pdf | sql | news` ayrımı, tipe özel
  opsiyonel alanlar), `AskResult` ve `CompareAskResult` genişletildi

---

### Adım 4 — SourceList Bileşeni

`frontend/src/components/SourceList.tsx` (yeni):

- Varsayılan kapalı, `Kaynaklar (7) · 4 sayfa` şeklinde özet buton
- **PDF/KAP kaynakları dosya bazında gruplanıyor**, sayfalar `s.12` `s.13` rozetleri
  olarak sıralı diziliyor; aynı sayfa birden fazla chunk'tan gelirse en yüksek skorlu
  olan tutuluyor
- Rozete tıklayınca o sayfanın snippet'i, bölümü ve eşleşme yüzdesi açılıyor
- Finansal veri (mavi, tablo adları + dönem aralığı) ve haberler (kehribar, başlık +
  dış link + tarih) ayrı bloklarda
- `Message.tsx`: her AI mesajının altına `<SourceList />`; ayrıca araç rozetlerine
  eksik olan `📰 Haber` tipi eklendi (önceden haber de "Vektör" görünüyordu)

---

### Adım 5 — Testler

`tests/test_sources.py` (yeni, 10 test):

- Dört kaynak tipinin de doğru alanları taşıması (vector sayfa+bölüm, pdf çoklu sayfa,
  sql tablo+dönem, news başlık+link)
- `source_type` yoksa `vector`'e düşmesi
- Snippet'in `SNIPPET_LENGTH`'te `…` ile kesilmesi
- 30 sonuçtan 12'ye kırpma ve skor sıralaması
- Boş `retrieved` → boş liste
- `sql_retriever` entegrasyon testi: geçici SQLite DB ile `pdf_tables` sorgusunun
  `pages: [12, 13]` ve `s.12, s.13` citation'ı üretmesi

---

### Çıktı Kriterleri ✅

- ✅ Her cevabın altında kullanılan kaynaklar, PDF'lerde sayfa numarasıyla görünüyor
- ✅ Sayfa rozetine tıklayınca modele giden alıntı metni açılıyor
- ✅ Dört kaynak tipi (KAP chunk / PDF tablosu / yfinance / haber) ayrı gösteriliyor
- ✅ 83 pytest testi, tümü geçiyor (önceki 73)
- ✅ `npx tsc --noEmit` hatasız

---

## 2026-08-03 — Pazartesi
**Kalıcılık Düzeltmesi ve Yatırımcı Profili**

Kullanıcı "portföyümü giriyorum, çıkıp girince siliniyor" dedi. İnceleme sonucu
portföyün **aslında Firestore'a yazıldığı**, sorunun hataların sessizce yutulması
olduğu ortaya çıktı. Aynı oturumda sohbet geçmişindeki bir gizlilik açığı kapatıldı
ve agent'ı kişiselleştiren yatırımcı profili eklendi.

---

### Adım 1 — Portföy "Siliniyor" Sorunu

**Teşhis:** `portfolioService.ts` portföyü `users/{uid}/portfolios/default` altında
tutuyor ve giriş Google ile olduğu için `uid` sabit — mimari doğruydu. Sorun
`PortfolioPage.tsx`'teki iki sessiz `catch`'ti:

- Okuma hatası → `.catch(() => setHoldings([]))` — kullanıcı **boş portföy** görüyor,
  hiçbir uyarı yok. "Silinmiş" izlenimi tam olarak buradan geliyordu.
- Yazma hatası → boş `catch` — ekranda hisse duruyor ama Firestore'a hiç gitmemiş;
  sonraki girişte kayboluyor.

**Çözüm:**
- `services/firebaseError.ts` (yeni): Firestore hata kodlarını Türkçe, eyleme dönük
  mesajlara çevirir (`permission-denied`, `unavailable`, `failed-precondition` vb.)
- Okuma hatasında `holdings` **boşaltılmıyor**; kehribar renkli uyarı + "Yeniden dene"
- Yazma hatasında "bu sayfadan çıkarsanız kaybolur" uyarısı
- Empty state artık yükleme sırasında ve hata varken gizli — yanlış "portföyün boş" mesajı yok
- `firestore.rules` (yeni) repoya eklendi (veritabanı oluşturulduktan sonra yüklenecek)

**Kök neden (kesin):** Firestore REST API'ye doğrudan sorgu atıldığında proje
`agentickio-5ed5f` için şu cevap geldi:

```
404 NOT_FOUND — The database (default) does not exist for project agentickio-5ed5f
```

Yani **Firestore veritabanı hiç oluşturulmamış**. Portföy silinmiyordu; hiçbir zaman
yazılmamıştı. İlk tahmin olan "güvenlik kuralları reddediyor" senaryosu yanlıştı —
kurallar ancak veritabanı var olduğunda devreye girer.

---

### Adım 2 — Sohbet Geçmişi Gizlilik Açığı

**Sorun:** `conversationStorage.ts` tüm sohbetleri tek bir `agentick_conversations`
anahtarında tutuyordu — **uid'e göre ayrılmamış**. Aynı bilgisayarda ikinci bir hesapla
giriş yapan kullanıcı, öncekinin bütün sohbetlerini görüyordu.

**Çözüm:**
- Anahtar `agentick_conversations_{uid}` oldu; tüm fonksiyonlar `uid` alıyor
- `migrateLegacy()` — eski anahtarsız kayıtlar ilk kullanıcıya bir kereliğine taşınır,
  ardından eski anahtar silinir (ikinci kullanıcıya sızmasın)
- `App.tsx`: kullanıcı değişince konuşma listesi ve aktif sohbet sıfırlanıyor

---

### Adım 3 — Yatırımcı Profili (Kişiselleştirme)

Profil, cevabın **hangi veriye ağırlık vereceğini** ve dilin ne kadar teknik olacağını
belirler. Dört alan: yaklaşım (temkinli/dengeli/agresif), vade (kısa/orta/uzun),
ilgi alanları (temettü/büyüme/değerleme/likidite, çoklu), finans bilgisi
(başlangıç/orta/ileri).

**Backend — `src/agent/user_profile.py` (yeni):**
- `sanitize_profile()` — istemciden gelen profili beyaz listeye indirger; bilinmeyen
  anahtar/değer sessizce atılır. Profil serbest metin taşımadığı için prompt injection
  yüzeyi yok.
- `apply_profile()` — talimatı system prompt'a **uyumluluk bloğundan ÖNCE** yerleştirir.
  Böylece SPK kuralları prompt'un son bölümü olarak kalır ve profil onları gölgeleyemez.
- Talimatın kendisi de açıkça yasaklıyor: tercihler "uygunluk değerlendirmesi" veya
  alım-satım yönlendirmesine dönüştürülemez.
- `state.py` `user_profile`, `graph.py` `run_agent(..., user_profile=)`, üç route'ta
  `profile` alanı + `sanitize_profile` çağrısı

**Frontend:**
- `services/profileService.ts` (yeni) — `users/{uid}/profile/default`, etiketler
- `contexts/ProfileContext.tsx` (yeni) — profil bir kez yüklenip sohbet / karşılaştırma
  / portföy sayfalarının üçüne birden dağıtılıyor
- `components/ProfileModal.tsx` (yeni) — Sidebar'daki kullanıcı bloğuna tıklayınca açılır;
  seçili seçeneğe tekrar basmak tercihi temizler
- Sidebar: profil doluysa avatarda yeşil nokta, boşsa "Profilini ayarla" çağrısı
- `client.ts`: üç ask fonksiyonu da opsiyonel `profile` gönderiyor

---

### Adım 4 — Doğrulama

Backend ayağa kaldırılıp aynı soru iki kez soruldu:

| | Profilsiz | Temkinli + likidite + yeni başlayan |
|---|---|---|
| Vurgu | Piyasa değeri, hisse fiyat aralığı, FAVÖK | Ciro, vergi öncesi kâr, kapasite kullanımı |
| Ek bölüm | — | "Kredi Derecelendirmesi ve **Finansal Yapı**" (bilanço/finansman politikası) |

Uyumluluk dipnotu her iki cevapta da yerinde.

---

### Not — Veri Etiketleme Hatası (kod hatası değil)

Test sırasında THYAO sorusuna Tüpraş verisi geldiği görüldü. Kaynak listesi sebebi
anında gösterdi: `THYAO_tupras-2025-entegre-faaliyet-raporu (1).pdf` — Tüpraş raporu
THYAO seçiliyken yüklenmiş. Retriever doğru çalışıyor, veri yanlış etiketlenmiş.
Bu kaydın yeniden yüklenmesi gerekiyor. (Kaynak gösterimi özelliğinin ilk somut faydası.)

---

### Çıktı Kriterleri ✅

- ✅ Portföy okuma/yazma hataları kullanıcıya gösteriliyor, sessiz veri kaybı yok
- ✅ `firestore.rules` repoda — kalıcılık sorununun kök nedeni dokümante
- ✅ Sohbetler kullanıcı bazında ayrı; eski kayıtlar tek seferlik taşınıyor
- ✅ Profil cevabın vurgusunu değiştiriyor, SPK uyumluluk bloğu bozulmuyor
- ✅ 105 pytest testi, tümü geçiyor (önceki 83) — 22 yeni profil testi
- ✅ `npx tsc --noEmit` hatasız

---

### Adım 5 — Profil Modalı Sonsuz "Yükleniyor" (aynı kök neden)

**Sorun:** Profil modalı açılınca dönen spinner hiç durmuyordu. İki sebep vardı:

1. Modal, `ProfileContext`'te zaten yüklenmiş profili **ikinci kez** çekiyordu
2. Firestore SDK, var olmayan veritabanına yaptığı isteği sessizce yeniden denemeye
   devam ediyor; promise ne çözülüyor ne reddediliyor → spinner sonsuza dek dönüyor

**Çözüm:**
- `withFirestoreTimeout()` (`firebaseError.ts`) — 8 saniyelik üst sınır, aşılırsa
  `deadline-exceeded` hatasına çevrilir. Portföy okuma/yazma da bu sarmalayıcıdan geçiyor.
- Modal artık kendi isteğini atmıyor; `ProfileContext`'ten okuyor → anında açılıyor
- `ProfileContext` `loading` / `error` / `reload` sunuyor; hata modalda
  "Yeniden dene" butonuyla gösteriliyor

---

### Adım 6 — Firestore Kurulumu ve Uçtan Uca Doğrulama

Veritabanı Firebase konsolundan oluşturuldu (Standard edition, `(default)` ID) ve
`firestore.rules` içeriği Rules sekmesine yüklenip yayınlandı.

Doğrulama zinciri:

| Aşama | Kanıt |
|---|---|
| Başlangıç | REST sorgusu `404 NOT_FOUND — database (default) does not exist` |
| Veritabanı oluşturuldu | Aynı sorgu `403 PERMISSION_DENIED` (kimliksiz istek reddediliyor) |
| Kurallar yayınlandı | Rules Playground: `get /users/{uid}/portfolios/default`, authenticated → **Simulated read allowed** |
| Uygulama | Hard refresh sonrası AKBNK + ARCLK eklendi, uyarı bandı çıkmadı |

**Ara not:** Kurallar yayınlanmadan önce açık olan sekme yazma denemişti; o an
varsayılan `if false` kuralı yürürlükteydi ve "izin reddedildi" bandı ekranda kalmıştı.
Banner yeni bir denemeye kadar temizlenmiyor — hard refresh ile çözüldü. Yeni hata
gösterimi olmasaydı bu durum yine sessiz bir veri kaybı olarak geçecekti.

---

### Sıradaki

- [ ] Yanlış etiketlenmiş THYAO/Tüpraş PDF kaydının temizlenip yeniden yüklenmesi
- [ ] Deployment (Railway + Vercel) — `ENVIRONMENT=production`, `FIREBASE_PRIVATE_KEY`,
      `CORS_ORIGINS` zorunlu

---

## 2026-08-04 — Salı
**Yasal Zemin / Gün 1 — SPK Sınırı: Neyi Satabiliriz, Neyi Satamayız**

> ⚠️ **Bu üç günlük bölüm hukuki görüş değildir.** Aşağıdakiler mevzuat metinleri ve
> ikincil kaynaklar üzerinden çıkarılmış çalışma notlarıdır. Ticarileşme öncesi sermaye
> piyasası hukuku alanında çalışan bir avukatla ve gerekirse SPK'ya yazılı görüş
> başvurusuyla teyit edilmelidir. Kaynaklar her bölümün sonunda.

Kod tarafı Sprint 3 ile oturdu. Ürünü ücretli hale getirmeden önce cevaplanması gereken
soru şu: **agentick.io'nun yaptığı iş SPK'ya göre lisans gerektiriyor mu?**

---

### Bulgu 1 — İki ayrı faaliyet var, aradaki çizgi "kişiye özel" olmak

Sermaye piyasası mevzuatı bu ikisini keskin biçimde ayırıyor:

| | Genel yatırım tavsiyesi | Yatırım danışmanlığı |
|---|---|---|
| Muhatap | Belirli bir kişi/gruba **yönelik değil** | Kişiye özel |
| Girdi | Kamuya açık veri, genel analiz | Müşterinin risk ve getiri tercihleri |
| Yetki belgesi | Gerekmiyor (koşullu) | **Zorunlu** |
| Örnek | "X'in net marjı %12,08" | "Sizin profilinize X uygun" |

Belirleyici ölçüt niyet değil, **çıktının kişiselleşme derecesi**. Aynı cümle, alıcının
risk profiline göre üretildiği anda faaliyet sınıfı değişiyor.

Ölçek fikri vermesi açısından: TSPB üye listesine göre 44 bankadan 2'si, 80 aracı
kurumdan 62'si, 53 portföy yönetim şirketinden 19'u yatırım danışmanlığı yetki belgesine
sahip. Yani belge sıradan bir kayıt işlemi değil, kurumsal bir eşik.

---

### Bulgu 2 — Mevcut kod bu çizginin doğru tarafında, ama teğet geçiyor

`synthesizer_node.py` içindeki uyumluluk bloğu (Faz 3'ten beri var) tam olarak bu ayrımı
koruyor: al/sat/tut yasak, değer yargısı yasak, hedef fiyat yasak, "X daha iyi" yerine
"X'in net marjı daha yüksek". Bu, ürünü **genel yatırım tavsiyesi** tarafında tutuyor.

Ancak 3 Ağustos'ta eklenen **yatırımcı profili** özelliği tam da bu sınırın üzerinde
duruyor. `user_profile.py` bunu bilinçli olarak şöyle sınırlıyor:

- Profil yalnızca **hangi verinin öne çıkacağını** ve dilin teknik seviyesini belirliyor
- `apply_profile()` talimatı uyumluluk bloğundan **önce** yerleştiriyor; SPK kuralları
  prompt'un son sözü olarak kalıyor
- Talimatın kendisi açıkça yasaklıyor: tercihler "uygunluk değerlendirmesine" veya
  alım-satım yönlendirmesine dönüştürülemez

**Değerlendirme:** Bu tasarım savunulabilir görünüyor — profil bir *sunum filtresi*,
*tavsiye üreteci* değil. Ama sınır ince. Riskli olacak yön: profile göre **hisse
sıralamak, filtrelemek veya öneri listesi üretmek**. Bunlar "kişiye özel" tanımına
girer. Screening/Alert özelliği (roadmap'te var) tasarlanırken bu eşiğe dikkat edilmeli.

---

### Bulgu 3 — Yapay zekâ için net bir çerçeve henüz yok

Türkiye'de "algoritmik tavsiye" ile "kişisel finansal danışmanlık" arasındaki sınır
düzenleyici metinlerde tanımlanmış değil. AB tarafında AI Act finansal yapay zekâyı
yüksek riskli sistem sayarken, Türkiye'de karşılığı henüz oluşmamış. Robo-danışmanlık
alanında bankalar ve fintech'ler faaliyette (QNB Akıllı Robo vb.) ama bunlar lisanslı
kuruluşların şemsiyesi altında.

**Pratik sonuç:** Boşluk, serbestlik anlamına gelmiyor — aksine, ihtilaf halinde
mevcut yatırım danışmanlığı tanımına göre değerlendirilme riski var. Muhafazakâr
konumlanma doğru tercih.

---

### Bu günün kararı

Ürün **"araştırma asistanı"** olarak konumlanacak, "danışman" olarak değil. Bu karar
yarınki veri/gizlilik analizini ve perşembe günkü fiyatlama modelini doğrudan
kısıtlıyor: kişiselleştirme satılabilir bir özellik ama **tavsiye** olarak
pazarlanamaz.

**Kaynaklar:**
- [SPK — Yatırım Danışmanlığı Yetki Belgesi Talebi](https://spk.gov.tr/kurumlar/portfoy-yonetim-sirketleri/basvuru-surecleri/yatirim-danismanligi-yetki-belgesi-talebi)
- [SPK — Yatırım Hizmetleri ve Kuruluşları Rehberi (i-SPK.37.8)](https://spk.gov.tr/data/61e496a11b41c60d1404d6b2/Yat%C4%B1r%C4%B1m%20Hizmetleri%20ve%20Kurulu%C5%9Flar%C4%B1%20Rehberi%20(i-SPK.37.8)%2010%2003%202026.pdf)
- [Anadolu Üniversitesi — Sermaye Piyasalarında Yatırım Danışmanlığı](https://avesis.anadolu.edu.tr/dosya?id=8d9f0fc5-fb60-4133-9b71-47e16acdc79e)
- [Fintechtime — Fintek'lerin Yapay Zekâ ile Dönüşüm Çerçevesi](https://fintechtime.com/2025/11/finteklerin-yapay-zeka-ai-ile-donusum-cercevesi/)

---

## 2026-08-05 — Çarşamba
**Yasal Zemin / Gün 2 — KVKK: Profil Verisi ve Firestore'un Nerede Durduğu**

Dünkü karar (kişiselleştirme var, tavsiye yok) doğrudan bir veri sorusu doğuruyor:
yatırımcı profili — risk yaklaşımı, vade, ilgi alanları — **kişisel veri**. Üstelik
kişinin finansal davranışına dair. Bu verinin nerede durduğu ve nasıl toplandığı
6698 sayılı KVKK kapsamında.

---

### Bulgu 1 — Firestore konumu bir "yurt dışına aktarım" kararıydı

3 Ağustos'ta Firestore veritabanı oluşturulurken seçilen bölge, farkında olmadan bir
KVKK kararıydı. Kurum'un yorumuna göre **yurt dışındaki bir bulutta depolama işlemi
aktarım sayılıyor** — ayrıca yurt dışında bulunan bir hesaba erişim hakkı verilmesi de.

Yani `users/{uid}/profile/default` belgesi hangi bölgedeyse, oraya aktarım yapılıyor.
Türkiye'de Firestore bölgesi yok; dolayısıyla **hangi bölge seçilirse seçilsin aktarım
gerçekleşiyor**. Soru "aktarım var mı" değil, "hangi güvenceyle" sorusuna dönüşüyor.

---

### Bulgu 2 — 2024 değişikliği sonrası mekanizma

7499 sayılı Kanun'un 34. maddesiyle KVKK m.9 değişti, **01.06.2024**'te yürürlüğe girdi.
Yönetmelik 10.07.2024 tarih ve 32598 sayılı Resmî Gazete'de yayımlandı. Standart
sözleşme metinleri Kurul'un 04.06.2024 tarihli 2024/959 sayılı kararıyla kabul edildi.

Aktarım için başvurulabilecek yollar:

1. **Yeterlilik kararı** — Kurul'un ilgili ülke için verdiği karar
2. **Uygun güvenceler** — standart sözleşme veya bağlayıcı şirket kuralları
3. **İstisnalar** — açık rıza dahil, dar kapsamlı ve arızi kullanım için

Bizim durumumuz için gerçekçi olan **standart sözleşme**. Standart sözleşme
imzalandığında Kurul'a bildirim yükümlülüğü doğuyor (imza tarihinden itibaren süreli).

**Not:** Kurul'un 2026 itibarıyla denetim odağını Bulut Bilişim / Yapay Zekâ / SaaS
alanlarına kaydırdığı görülüyor. agentick.io bu üçünün kesişiminde duruyor — yani
düşük öncelikli bir hedef değil.

---

### Bulgu 3 — Eksik olan üç şey

Kod tarafı hazır ama hukuki katman boş:

| Gereklilik | Durum |
|---|---|
| Aydınlatma metni (KVKK m.10) | ❌ Yok |
| Açık rıza akışı (profil verisi için) | ❌ Yok — profil kaydı rızasız alınıyor |
| Gizlilik politikası / KVKK metni | ❌ Yok |
| Standart sözleşme (Google/Firebase) | ❌ İmzalanmadı, Kurul'a bildirilmedi |
| VERBİS kaydı | ❓ Eşik değerlendirmesi yapılmadı |
| Veri saklama/imha politikası | ❌ Yok |
| Erişim kontrolü | ✅ `firestore.rules` — `users/{uid}` sadece sahibine |
| Şifreleme (aktarım + durağan) | ✅ Firestore varsayılan |

Teknik güvenlik tarafı iyi durumda; **belge ve süreç tarafı tamamen eksik.**

---

### Bulgu 4 — Sohbet geçmişi de veri

3 Ağustos'ta `agentick_conversations_{uid}` düzeltmesi yapılmıştı — aynı bilgisayarda
ikinci kullanıcının öncekinin sohbetlerini görmesi engellendi. KVKK açısından bu bir
**veri ihlali riskiydi** ve düzeltilmesi isabetli. Ancak sohbetler hâlâ localStorage'da;
kullanıcının silme talebi (KVKK m.11) geldiğinde sunucu tarafında silinecek bir kayıt
yok — ki bu şu an lehimize, ama Firestore'a taşınırsa imha süreci tanımlanmalı.

---

### Bu günün kararı

Ücretli sürüm öncesi **kesinlikle** tamamlanması gerekenler: aydınlatma metni, profil
için açık rıza akışı, gizlilik politikası, Google ile standart sözleşme + Kurul bildirimi.

Bu, yarınki ticari analizi doğrudan etkiliyor: bu dört kalem **lansman öncesi sabit
maliyet** ve gecikme kalemi olarak modele girmeli.

**Kaynaklar:**
- [KVKK — Kişisel Verilerin Yurt Dışına Aktarılması Rehberi (Yayın No: 48)](https://www.kvkk.gov.tr/Icerik/8142/Kisisel-Verilerin-Yurt-Disina-Aktarilmasi-Rehberi)
- [KVKK — Yurt Dışına Aktarım](https://www.kvkk.gov.tr/Icerik/2053/Yurtdisina-Aktarim)
- [KVKK — Standart Sözleşme Metinleri Duyurusu](https://www.kvkk.gov.tr/Icerik/7998/Standart-Sozlesme-Metinlerinin-Ingilizce-Cevirisine-Iliskin-Duyuru)
- [Paksoy — Yurt dışına veri aktarımlarına ilişkin yeni yönetmelik](https://paksoy.av.tr/2024/07/kisisel-verileri-koruma-kurumu-yurt-disina-veri-aktarimlarina-iliskin-yeni-bir-yonetmelik-yayimladi/)
- [GSG Hukuk — Yönetmelik yürürlüğe girdi](https://www.gsghukuk.com/tr/bultenler-yayinlar/duyurular/kisisel-verilerin-yurt-disina-aktarilmasina-iliskin-usul-ve-esaslar-hakkinda-yonetmelik-yururluge-girdi.html)

---

## 2026-08-06 — Perşembe
**Ticari Yol Haritası — İki Günlük Hukuki Kısıtın İçinde Model Kurmak**

Salı ve çarşamba iki sınır çizdi:

1. **Tavsiye satılamaz** → değer önerisi "karar verdirme" değil, "araştırma süresini kısaltma"
2. **Profil verisi rıza + belge gerektiriyor** → kişiselleştirme lansmanın kritik yolunda

Bugün bu iki kısıtın içinde ticari model çalışıldı.

---

### Rekabet konumu

Türkiye'de mevcut oyuncular iki uçta toplanmış:

| Segment | Örnek | Sunduğu | Boşluk |
|---|---|---|---|
| Aracı kurum / işlem | Midas | Komisyonsuz BIST işlemi, canlı veri | Analiz yüzeysel |
| Profesyonel terminal | Matriks IQ, Foreks | Derin veri, gelişmiş grafik | Pahalı, öğrenme eğrisi dik, **doküman okumuyor** |

**Boşluk:** İkisi de 500 sayfalık faaliyet raporunu okuyup "bu bilgi s.442'de" demiyor.
agentick.io'nun kaynak gösterimi (31 Temmuz) tam olarak bu boşluğa oturuyor — ve
tavsiye vermediği için Salı'daki kısıtı da ihlal etmiyor.

**Konumlandırma cümlesi:** *"Terminal fiyatına değil, araştırma süresine odaklanan
kaynaklı analiz."*

---

### Birim ekonomi — bilinenler ve bilinmeyenler

Elimizde ölçülmüş veri var (3 Ağustos testlerinden):

- Sentez modeli: Claude Haiku 4.5, soru başına 1500–2500 çıktı token'ı
- Retriever: 12 kaynak × ~240 karakter snippet + tam chunk metni
- Agent zinciri: planner → router → critic → synthesizer, retry olabiliyor

**Henüz ölçülmedi:** soru başına gerçek $ maliyeti. Fiyatlama bunun üzerine kurulacağı
için **ilk yapılacak iş bu** — LangSmith zaten bağlı, trace'lerden token maliyeti
çıkarılabilir.

Sabit maliyetler: Qdrant Cloud (ücretsiz tier şimdilik yetiyor), Firebase Spark plan
(`$0/ay` — ekran görüntüsünde görünüyor, ölçekte Blaze'e geçiş gerekecek), hosting.

**Hukuki sabit maliyet (çarşambadan):** avukat görüşü + aydınlatma/gizlilik metinleri +
standart sözleşme süreci. Bu kalem lansman tarihini belirleyen kritik yolda.

---

### Fiyatlama iskeleti (taslak)

| Katman | İçerik | Gerekçe |
|---|---|---|
| Ücretsiz | Günlük N soru, tek hisse, kaynak gösterimi | Ürünün farkı ilk 5 dakikada anlaşılmalı |
| Bireysel | Sınırsız soru, karşılaştırma, portföy, **profil** | Profil = rıza akışı gerektiren katman |
| Profesyonel | Toplu doküman yükleme, dışa aktarma, API | Sonraki faz |

Kritik tasarım kararı: **profil özelliği ücretli katmanda** olmalı. Sebep ticari değil,
hukuki — rıza akışı ve aydınlatma yükümlülüğü yalnızca o katmanda devreye girer, ücretsiz
kullanıcıda kişisel veri işleme yüzeyi minimumda kalır.

---

### Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| SPK'nın kişiselleştirmeyi danışmanlık sayması | Yüksek | Profil = sunum filtresi; screening/öneri listesi yapılmayacak |
| KVKK denetimi (SaaS/AI odağı) | Yüksek | Lansman öncesi belge seti + standart sözleşme |
| LLM maliyetinin fiyatı aşması | Orta | Ölçüm önce, fiyat sonra; cache ve model kademelendirme |
| Veri kaynağı (yfinance) ticari kullanım şartları | **Belirsiz** | Araştırılmadı — yarına |
| KAP verisinin yeniden yayını | **Belirsiz** | Araştırılmadı — yarına |

Son iki satır bugünkü çalışmanın açık ucu. Ticari kullanımda veri kaynağı lisansı,
SPK ve KVKK kadar belirleyici olabilir.

**Kaynaklar:**
- [Midas — Ücretler & Komisyon Oranları](https://www.getmidas.com/ucretler/)
- [Matriks Data — Finansal Veri & Analiz](https://www.matriksdata.com/website/)
- [Osmanlı Menkul — Data ve Platform Kullanım Ücretleri](https://www.osmanlimenkul.com.tr/hisse-ve-viop/platformlarimiz/canli-data-ve-platformlar/data-ve-platform-kullanim-ucretleri)

---

## 2026-08-07 — Cuma — 📋 PLAN (henüz yapılmadı)

> Bu bölüm **yapılacaklar listesidir**, tamamlanmış iş kaydı değildir. Gün sonunda
> gerçekleşene göre yeniden yazılacak.

Perşembe günü iki soru açık kaldı; cuma bunlarla başlıyor.

### 1. Veri kaynağı lisansları (açık uç)

- [ ] yfinance / Yahoo Finance kullanım şartları — ticari kullanım açıkça yasak mı?
      Yasaksa lisanslı veri sağlayıcı alternatifleri ve maliyetleri
- [ ] KAP verisinin yeniden yayınlanma koşulları
- [ ] Haber RSS kaynaklarının içerik kullanım şartları (özet çıkarma / alıntılama)

### 2. Ölçüm

- [ ] LangSmith trace'lerinden **soru başına gerçek maliyet** çıkarılması
      — fiyatlama bunun üzerine kurulacak, tahminle ilerlenmeyecek

### 3. Hukuki belge seti — ilk taslaklar

- [ ] Aydınlatma metni taslağı
- [ ] Profil verisi için açık rıza akışı (UI + metin)
- [ ] Gizlilik politikası taslağı
- [ ] VERBİS kayıt eşiği değerlendirmesi

### 4. Doğrulama

- [ ] Sermaye piyasası hukuku alanında avukat görüşmesi için soru listesi hazırlanması
      — özellikle: profil özelliği "kişiye özel tavsiye" sayılır mı?

---
