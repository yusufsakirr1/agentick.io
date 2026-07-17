# agentick.io — Roadmap

---

## FAZ 1 — Veri Katmanı + Naive RAG
**Hedef:** KAP'tan PDF indir, Türkçe soruya kaynaklı cevap ver.

- [x] Proje klasörü ve bağımlılık kurulumu (`uv init`, `pyproject.toml`, `.env`)
- [x] `kap_client.py` — THYAO faaliyet raporunu KAP'tan indir
- [x] `pdf_chunker.py` — Türkçe PDF'i chunk'la, metadata ekle
- [x] `build_vector_index.py` — Qdrant Cloud free tier'a embedding yaz
- [x] CLI test — "THY'nin 2026 finansal sonuçları?" sorusuna cevap geldi

**Geçiş kriteri:** Tek kaynaklı Türkçe soruya doğru, kaynaklı cevap geliyor. ✅

---

## FAZ 2 — Çoklu Retriever Katmanı
**Hedef:** 4 retriever bağımsız çalışsın.

- [ ] `bist_finance_client.py` — yfinance `.IS` suffix ile BIST finansal veri
- [ ] `sql_retriever.py` — text-to-SQL ile sayısal sorgular
- [ ] `news_retriever.py` — Claude web_search ile Türkçe haber
- [ ] `kap_event_retriever.py` — KAP özel durum bildirimleri
- [ ] Her retriever `RetrievalResult` formatında test edildi

**Geçiş kriteri:** 4 retriever bağımsız test dosyasında doğru format dönüyor.

---

## FAZ 3 — LangGraph Agent Orkestrasyonu
**Hedef:** Retriever'ları agent grafına bağla.

- [ ] `state.py` — AgentState tanımı
- [ ] `planner_node.py` — soruyu alt görevlere böl
- [ ] `router_node.py` — asyncio.gather ile paralel retriever çağrısı
- [ ] `graph.py` — LangGraph bağlantısı (START → planner → router → critic → synthesizer → END)

**Geçiş kriteri:** Çok adımlı soru otomatik alt görevlere bölünüp doğru kaynağa yönleniyor.

---

## FAZ 4 — Self-Critique / Retry Döngüsü
**Hedef:** Agent kendi eksikliğini fark edip ek arama yapsın.

- [ ] `critic_node.py` — bilgi yeterli mi? JSON çıktı
- [ ] Retry döngüsü — `retry_count >= 3` ise kır
- [ ] `add_conditional_edges` ile döngü graf'a bağlandı

**Geçiş kriteri:** Eksik bilgi senaryosunda Critic ek arama tetikliyor.

---

## FAZ 5 — Synthesizer + Kaynak Gösterme
**Hedef:** Türkçe, tutarlı, kaynaklı nihai cevap.

- [ ] `synthesizer_node.py` — her cümleyi kaynağa bağla
- [ ] KAP URL'leri citation'a eklendi
- [ ] Çelişkili veri açıkça belirtiliyor

**Geçiş kriteri:** Cevabın her iddiası bir KAP belgesine veya yfinance verisine bağlı.

---

## FAZ 6 — Auth + Freemium + Stripe
**Hedef:** Gerçek kullanıcıya açılabilecek minimum altyapı.

- [ ] Supabase projesi + Auth (email/Google)
- [ ] `user_quotas` tablosu (5 ücretsiz sorgu/ay)
- [ ] `quota.py` FastAPI middleware
- [ ] Stripe Payment Link — Pro abonelik

**Geçiş kriteri:** Kullanıcı kaydolup 5 sorgu kullanabiliyor, 6.'da ödeme sayfasına yönleniyor.

---

## FAZ 7 — Next.js Frontend
**Hedef:** Satılabilir, profesyonel UI.

- [ ] Next.js + shadcn/ui kurulum
- [ ] `/app` — ticker gir + soru yaz + SSE ile streaming cevap
- [ ] Trace paneli (yan kolon — adım adım agent süreci)
- [ ] `/` — ana sayfa + değer önerisi
- [ ] `/pricing` — Free vs Pro

**Geçiş kriteri:** Mobil uyumlu, trace panelli, canlı akışlı UI çalışıyor.

---

## FAZ 8 — Eval Sistemi
**Hedef:** Cevap kalitesini ölç.

- [ ] `bist_test_questions.jsonl` — 20-30 BIST sorusu (tek kaynak / çok kaynak / tuzak)
- [ ] `run_eval.py` — naive RAG vs agentic RAG karşılaştırma
- [ ] Metrikler: doğruluk, citation coverage, retry sayısı, yanıt süresi

---

## FAZ 9 — Lansman
**Hedef:** İlk gerçek kullanıcılar.

- [ ] İlk 20 BIST-30 hissesi için KAP verisi yüklendi
- [ ] Langfuse ile LLM gözlemlenebilirlik aktif
- [ ] Railway deployment canlı
- [ ] Reddit r/Borsasi paylaşımı
- [ ] Twitter/X `#BIST` paylaşımı
- [ ] İlk 50 kullanıcı → feedback döngüsü başladı
