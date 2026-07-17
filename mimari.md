# agentick.io — BIST için Agentic AI Finansal Analist

> **Ürün:** Türk bireysel yatırımcıların BIST hisseleri hakkında soru sorabildiği,
> KAP dosyaları, finansal tablolar ve güncel haberlerden kaynaklı cevap alan
> Türkçe AI finansal analiz platformu.
>
> **Hedef kitle:** Temel analiz yapmaya çalışan ama araç ve zaman kısıtı olan
> Türk bireysel yatırımcısı.
>
> **İş modeli:** Freemium SaaS — ayda 5 sorgu ücretsiz, sonrası aylık ₺199 / $9.
>
> **Rekabet avantajı:** KAP verileri + Türkçe içerik + agentic reasoning.
> Bloomberg/Perplexity bu nişi karşılamıyor.

---

## 1. Genel Mimari

```
                          ┌─────────────────────┐
                          │   Kullanıcı Sorusu   │
                          │  (Türkçe, BIST odak) │
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼───────────┐
                          │   PLANNER NODE        │
                          │ Soruyu alt görevlere  │
                          │ böler, kaynak tipini  │
                          │ sınıflandırır         │
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼───────────┐
                          │   ROUTER NODE         │
                          │ Her alt görev için    │
                          │ doğru kaynağı seçer   │
                          └──────────┬───────────┘
           ┌─────────────────────────┼──────────────────────┬────────────────────┐
           │                         │                        │                    │
    ┌──────▼──────┐         ┌────────▼──────┐       ┌────────▼──────┐   ┌────────▼──────┐
    │ SQL/Numeric  │         │  Vector RAG   │        │  Haber/Web    │   │  KAP Özel     │
    │  Retriever   │         │ (KAP Faaliyet │        │  Retriever    │   │  Durum        │
    │  (yfinance   │         │  Raporları)   │        │  (TR haber    │   │  Retriever    │
    │   BIST .IS)  │         │               │        │   kaynakları) │   │  (özel durum, │
    └──────┬──────┘         └────────┬──────┘        └────────┬──────┘   │  YK kararları)│
           └─────────────────────────┼───────────────────────┘    └────────┬──────┘
                                     │                                      │
                                     └──────────────────────────────────────┘
                                                      │
                                          ┌──────────▼───────────┐
                                          │  CRITIC NODE          │
                                          │ Sonuç yeterli mi?     │
                                          │ Yetersizse → Router'a │
                                          │ geri dön (max 3 tur)  │
                                          └──────────┬───────────┘
                                                     │ yeterli
                                          ┌──────────▼───────────┐
                                          │  SYNTHESIZER NODE     │
                                          │ Türkçe, kaynak        │
                                          │ göstererek nihai      │
                                          │ cevabı üretir         │
                                          └──────────┬───────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │   Cevap + Trace Log   │
                                          │   + KAP linkleri      │
                                          └───────────────────────┘
```

Graf **LangGraph** ile kurulur. Her node Python fonksiyonu, geçişler conditional.
Critic node retry/devam kararı verir — sonsuz döngüye karşı `MAX_RETRY_COUNT=3`.

---

## 2. Veri Kaynakları

| Retriever | Kaynak | Ne çeker |
|---|---|---|
| SQL/Numeric | `yfinance` (`.IS` suffix) | Fiyat, gelir tablosu, bilanço, marj, F/K, PD/DD |
| Vector RAG | KAP.org.tr — faaliyet raporları (PDF) | Yönetim yorumu, strateji, risk faktörleri |
| Haber/Web | Bloomberg HT, Dünya, Reuters TR, Milliyet Ekonomi | Güncel gelişmeler, sektör haberleri |
| KAP Özel Durum | KAP.org.tr — özel durum bildirimleri, YK kararları | Temettü, sermaye artırımı, ortaklık değişimi |

**KAP veri erişimi:** Resmi API yok. Veriler herkese açık, scraping legaldir.
`kap.org.tr` URL yapısı tahmin edilebilir — şirket kodu + belge tipi ile çekilir.

---

## 3. Teknoloji Stack

| Katman | MVP (İlk Lansman) | Sonraki Aşama |
|---|---|---|
| Agent orkestrasyonu | **LangGraph** | LangGraph (değişmez) |
| LLM | **Claude claude-sonnet-4-6** | claude-sonnet-4-6 (değişmez) |
| Embedding | **voyage-3** | voyage-3 |
| Vektör DB | **Qdrant Cloud** (free tier) | Qdrant Cloud (ölçekle) |
| İlişkisel DB | **Supabase** (PostgreSQL) | Supabase |
| Auth | **Supabase Auth** | Supabase Auth |
| Backend | **FastAPI** | FastAPI |
| Frontend | **Next.js + shadcn/ui** | Next.js |
| Ödeme | **Stripe** | Stripe |
| LLM gözlemlenebilirlik | **Langfuse** (self-host) | Langfuse |
| Deployment | **Railway** | Railway / Fly.io |
| Ortam | **uv** | uv |

**Neden Streamlit değil:** Perakende yatırımcıya satılacak bir ürün için Streamlit
yeterince profesyonel görünmüyor. Next.js ile mobil uyumlu, hızlı bir UI.

---

## 4. Klasör Yapısı

```
agentick.io/
├── mimari.md
├── .env.example
├── pyproject.toml
├── data/
│   ├── raw/                        ← KAP'tan indirilen PDF'ler
│   ├── processed/                  ← chunk'lanmış, temizlenmiş metin
│   └── bist_financials.db          ← geliştirme için lokal SQLite
├── src/
│   ├── ingestion/
│   │   ├── kap_client.py           ← KAP.org.tr'dan faaliyet raporu + özel durum çekme
│   │   ├── bist_finance_client.py  ← yfinance .IS suffix ile BIST fiyat/finansal veri
│   │   ├── pdf_chunker.py          ← Türkçe PDF'leri chunk'lama
│   │   └── build_vector_index.py   ← Qdrant'a embedding yazma
│   ├── retrievers/
│   │   ├── sql_retriever.py        ← yfinance verisi, text-to-SQL
│   │   ├── vector_retriever.py     ← Qdrant semantic search
│   │   ├── news_retriever.py       ← TR haber kaynakları
│   │   └── kap_event_retriever.py  ← Özel durum bildirimleri
│   ├── agent/
│   │   ├── state.py                ← LangGraph AgentState
│   │   ├── planner_node.py
│   │   ├── router_node.py
│   │   ├── critic_node.py
│   │   ├── synthesizer_node.py
│   │   └── graph.py
│   ├── api/
│   │   ├── main.py                 ← FastAPI endpoints
│   │   ├── auth.py                 ← Supabase Auth middleware
│   │   └── quota.py                ← Freemium sorgu kotası kontrolü
│   └── ui/                         ← Next.js projesi (ayrı klasör)
├── eval/
│   ├── bist_test_questions.jsonl   ← BIST'e özel soru seti
│   ├── run_eval.py
│   └── results/
└── tests/
    ├── test_retrievers.py
    └── test_agent_graph.py
```

---

## 5. Retriever Standart Çıktı Formatı

```python
class RetrievalResult(TypedDict):
    source_type: str      # "sql" | "vector_kap" | "news" | "kap_event"
    content: str
    citation: str         # "KAP — THYAO Faaliyet Raporu 2024, s.47"
    url: str | None       # direkt KAP linki veya haber URL'i
    date: str | None      # verinin tarihi (tazelik için önemli)
    confidence: float
```

---

## 6. AgentState

```python
class AgentState(TypedDict):
    question: str
    ticker: str | None          # THYAO, TUPRS, ASELS vb.
    sub_tasks: list[str]
    retrieved: list[RetrievalResult]
    critic_feedback: str | None
    retry_count: int
    final_answer: str | None
    trace: list[dict]           # UI'daki adım adım trace için
    user_id: str                # Supabase user — kota kontrolü için
```

---

## 7. FAZ 1 — Veri Katmanı + Naive RAG (3-4 gün)

**Hedef:** Tek şirket, tek kaynak (KAP faaliyet raporu) üzerinde çalışan basit RAG.
Agentic kısım yok — boru hattının çalıştığını önce doğrula.

### Adımlar
1. `kap_client.py`: Türk Hava Yolları (THYAO) son faaliyet raporunu KAP'tan indir.
   - URL yapısı: `https://www.kap.org.tr/tr/Bildirim/{bildirim_id}`
   - Şirket sayfasından son yıllık raporu bul, PDF indir.
2. `pdf_chunker.py`: Türkçe PDF'i temizle ve chunk'la.
   - Chunk boyutu: ~500-800 token, %10-15 overlap.
   - Bölüm başlıklarını ("Finansal Durum", "Risk Faktörleri") metadata olarak sakla.
3. `voyage-3` ile embedding üret, **Qdrant Cloud** free tier'a yaz.
4. CLI ile test: "THY'nin 2024 yolcu gelirleri nedir?" → chunk → LLM → cevap.

**Çıktı kriteri:** Tek kaynaklı Türkçe sorulara doğru, kaynaklı cevap geliyor.

---

## 8. FAZ 2 — Çoklu Retriever Katmanı (3-4 gün)

**Hedef:** 4 retriever'ı bağımsız olarak çalışır hale getir. Aralarında henüz
agentic seçim yok — her biri ayrı test edilecek.

### Adımlar
1. **SQL Retriever** — `bist_finance_client.py`
   - `yfinance`: `yf.Ticker("THYAO.IS")` ile gelir tablosu, bilanço, oranlar.
   - Supabase PostgreSQL'e yaz (lokal geliştirmede SQLite kabul edilebilir).
   - LLM ile text-to-SQL: "THY'nin son 3 yılda F/K oranı nasıl değişti?" → SQL → sonuç.

2. **Vector RAG** — `vector_retriever.py`
   - Qdrant'ta semantic search.
   - Metadata filtresi: ticker + belge tipi + yıl.

3. **Haber Retriever** — `news_retriever.py`
   - Claude'un `web_search` tool'u ile Türkçe haber arama.
   - Arama deseni: `"{ticker} {şirket adı} site:bloomberght.com OR site:dunya.com"`

4. **KAP Özel Durum Retriever** — `kap_event_retriever.py`
   - KAP'taki özel durum bildirimleri listesini çek (temettü, sermaye, ortaklık).
   - Tarih bazlı filtrele (son 3 ay varsayılan).

**Çıktı kriteri:** Her retriever bağımsız test dosyasında doğru format dönüyor.

---

## 9. FAZ 3 — Agent Orkestrasyonu / LangGraph (3-4 gün)

**Hedef:** Faz 1-2 parçalarını gerçek graf'a bağla.

### Graf Akışı
```
START → planner → router → critic → (yetersizse) → router
                               │
                          (yeterliyse)
                               ▼
                          synthesizer → END
```

### Planner Node
- Girdi: Türkçe kullanıcı sorusu + ticker (varsa).
- Görev: 1-4 alt görev üret. Her görev için kaynak tipini sınıflandır:
  - Sayısal/oran/tarih → `sql`
  - Yönetim yorumu/strateji → `vector_kap`
  - Güncel/son gelişme → `news`
  - Temettü/sermaye/ortaklık → `kap_event`
- Çıktı: `sub_tasks` listesi + her biri için `source_type`.

### Router Node
- Her `sub_task` için ilgili retriever'ı `asyncio.gather` ile paralel çağır.
- Sonuçları `retrieved` listesine ekle.

**Çıktı kriteri:** "THYAO'nun son çeyrek kargo gelirleri ve yönetim bu konuda
ne dedi?" sorusu otomatik olarak SQL + vector görevlere bölünüyor.

---

## 10. FAZ 4 — Self-Critique / Retry Döngüsü (2-3 gün)

**Hedef:** Agent kendi sonucunu değerlendirip eksik bilgiyi fark etsin.

### Adımlar
1. **Critic Node**: Toplanan `retrieved` + orijinal soruyu LLM'e ver:
   - "Bu bilgi Türk yatırımcının sorusunu tam cevaplamak için yeterli mi?"
   - Yetersizse: neyin eksik olduğunu ve hangi kaynağın deneneceğini JSON döndür.
2. `retry_count >= 3` ise döngüyü kır — elde olanla "eksik bilgi" notu ile cevap üret.
3. Her retry'da yeni sorgu önceki state'e eklenir, kaybolmaz.

**Çıktı kriteri:** Kasıtlı eksik bırakılan bir senaryoda Critic ek arama tetikliyor.

---

## 11. FAZ 5 — Synthesizer + Kaynak Gösterme (1-2 gün)

**Hedef:** Tüm bilgiyi Türkçe, tutarlı, kaynaklı tek cevaba dönüştür.

### Adımlar
1. Synthesizer prompt'u her cümleyi ilgili `RetrievalResult`'a bağlasın:
   - `[Kaynak: KAP — THYAO Faaliyet Raporu 2024, s.23]`
   - `[Kaynak: yfinance — Gelir Tablosu Q3 2024]`
2. Cevap + citation listesi + KAP URL'leri ayrı alanlar olarak dönsün.
3. Çelişkili veri varsa (haberde bir rakam, raporda başka) açıkça belirt.

---

## 12. FAZ 6 — Auth + Freemium Kota + Stripe (3-4 gün)

**Hedef:** Ürünü gerçek kullanıcıya açmak için minimum altyapı.

### Adımlar
1. **Supabase Auth**: Email/Google ile kayıt/giriş.
2. **Kota tablosu** (`user_quotas`): Her kullanıcı için aylık sorgu sayısı.
   - Free tier: 5 sorgu/ay
   - Pro tier: sınırsız
3. **FastAPI middleware** (`quota.py`): Her sorgu öncesi kota kontrol et.
4. **Stripe**: Aylık abonelik linki (Stripe Payment Link — en hızlı entegrasyon).
   - Pro geçişte Supabase'de `tier = 'pro'` güncelle.

---

## 13. FAZ 7 — Next.js Frontend (3-5 gün)

**Hedef:** Perakende yatırımcıya satılabilecek, profesyonel görünümlü UI.

### Sayfalar
1. **Ana sayfa** (`/`): Değer önerisi + CTA ("Ücretsiz Dene")
2. **Uygulama** (`/app`): Ticker gir + soru yaz + cevap al
3. **Trace paneli** (yan kolonda): Planner alt görevleri, hangi kaynağa gidildi,
   kaç retry, hangi KAP belgesi kullanıldı — yatırımcı güven için şeffaflık kritik.
4. **Fiyatlandırma** (`/pricing`): Free vs Pro

### Teknik Notlar
- `shadcn/ui` ile hızlı bileşen kurulumu
- Server-Sent Events (SSE) ile streaming yanıt — yanıt bekletmez, satır satır gelir
- Mobil uyumlu — Türk yatırımcısı mobil ağırlıklı

---

## 14. FAZ 8 — Eval Sistemi (2-3 gün)

**Hedef:** Cevap kalitesini ölçüp iterasyon için temel oluştur.

### BIST Soru Seti (`bist_test_questions.jsonl`)
- 20-30 soru, 3 kategori:
  - Tek-kaynaklı: "THYAO'nun 2024 net marjı nedir?"
  - Çok-kaynaklı: "TUPRS'ın son 3 yılda temettü politikası ve bu dönemdeki kârlılık trendi nasıl?"
  - Tuzak: "Şirket hiç açıklamadığı bir konuda" — "bilmiyorum" demeli

### Metrikler
- Doğruluk (LLM-as-judge, Türkçe)
- Citation coverage (her cevabın kaç % KAP'a dayalı)
- Ortalama retry sayısı
- Yanıt süresi (hedef: <15 sn)

---

## 15. FAZ 9 — Lansman (1 hafta)

1. İlk 20 BIST hissesi için KAP verisi yükle (BIST-30 başlangıç için yeterli).
2. `agentick.io` canlıya al (Railway deployment).
3. Langfuse ile LLM çağrılarını izle (maliyet + kalite).
4. Dağıtım kanalları:
   - Reddit: r/Borsasi, r/TurkishInvestors
   - Twitter/X: `#BIST`, `#borsa`, `#yatırım`
   - Discord: Türk yatırımcı toplulukları
5. İlk 50 kullanıcı → feedback topla → iterate.

---

## 16. Ortam Değişkenleri (.env.example)

```
# LLM
ANTHROPIC_API_KEY=

# Embedding
VOYAGE_API_KEY=
EMBEDDING_MODEL=voyage-3

# Vector DB
QDRANT_URL=
QDRANT_API_KEY=

# Database & Auth
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Ödeme
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# KAP scraping
KAP_REQUEST_DELAY_SECONDS=2   # Rate limiting

# Agent
MAX_RETRY_COUNT=3

# LLM Gözlemlenebilirlik
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

---

## 17. Maliyet Tahmini (Aylık, 100 Pro Kullanıcı)

| Kalem | Tahmini Maliyet |
|---|---|
| Claude API (100 kullanıcı × 50 sorgu × ~4 LLM çağrısı) | ~$40-80 |
| Voyage-3 embedding | ~$5 |
| Qdrant Cloud | $0 (free tier başlangıç) |
| Supabase | $0 (free tier) |
| Railway deployment | ~$5-10 |
| **Toplam** | **~$50-100/ay** |

100 Pro kullanıcı × ₺199 = **~₺20.000/ay gelir** karşısında sürdürülebilir.

---

## 18. Riskler

| Risk | Önlem |
|---|---|
| KAP site yapısı değişir | Scraper'ı modüler yaz, URL yapısını config'den oku |
| Sonsuz retry | `MAX_RETRY_COUNT=3`, test edilmeli |
| Yüksek LLM maliyeti | Planner/router için claude-haiku-4-5, sadece synthesizer'da sonnet |
| Yanlış finansal bilgi | Her cevaba "Bu bilgi yatırım tavsiyesi değildir" notu + KAP linkleri zorunlu |
| BIST dışı soru | Ticker yoksa veya BIST dışı ise "Bu soru kapsam dışıdır" cevabı |

---

## 19. Faz Özeti

| Faz | İçerik | Süre |
|---|---|---|
| 1 | KAP veri katmanı + naive RAG | 3-4 gün |
| 2 | 4 retriever bağımsız çalışır | 3-4 gün |
| 3 | LangGraph agent orkestrasyonu | 3-4 gün |
| 4 | Self-critique / retry döngüsü | 2-3 gün |
| 5 | Synthesizer + kaynak gösterme | 1-2 gün |
| 6 | Auth + Freemium + Stripe | 3-4 gün |
| 7 | Next.js frontend | 3-5 gün |
| 8 | Eval sistemi | 2-3 gün |
| 9 | Lansman | 3-5 gün |

**Toplam:** ~6-8 hafta (günde 3-4 saat)

---

## 20. Agentic RAG ile Yapılabilecekler (Sonraki Özellikler)

| Özellik | Açıklama |
|---|---|
| Şirket karşılaştırma | "THYAO vs PEGASUS — marj ve büyüme karşılaştır" |
| Temettü takvimi | KAP özel durum + yfinance — otomatik temettü özeti |
| Haber etkisi analizi | "Bu haber hisseye nasıl etki etti?" — haber + fiyat korelasyonu |
| Sektör analizi | Havacılık sektörü genelinde birden fazla şirketi karşılaştır |
| Portföy analizi | Kullanıcının birden fazla hissesini aynı anda analiz et |
| Fiyat alarmı + özet | Hisse belirli seviyeye gelince KAP özetini otomatik gönder |
| PDF export | Analiz sonucunu kaynaklı PDF olarak indir |
