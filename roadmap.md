# agentick.io — Roadmap

---

## FAZ 1 — Veri Katmanı + Naive RAG ✅
**Hedef:** KAP'tan PDF indir, Türkçe soruya kaynaklı cevap ver.

- [x] Proje klasörü ve bağımlılık kurulumu (`uv init`, `pyproject.toml`, `.env`)
- [x] `kap_client.py` — THYAO faaliyet raporunu KAP'tan indir
- [x] `pdf_chunker.py` — Türkçe PDF'i chunk'la, metadata ekle
- [x] `build_vector_index.py` — Qdrant Cloud free tier'a embedding yaz
- [x] CLI test — "THY'nin 2026 finansal sonuçları?" sorusuna cevap geldi

**Geçiş kriteri:** Tek kaynaklı Türkçe soruya doğru, kaynaklı cevap geliyor. ✅

---

## FAZ 2 — SQL Retriever (yfinance + SQLite + text-to-SQL) ✅
**Hedef:** Yapılandırılmış finansal verilere SQL ile erişim.

- [x] `bist_finance_client.py` — yfinance `.IS` suffix ile BIST finansal veri → SQLite
- [x] `sql_retriever.py` — Claude Haiku ile text-to-SQL dönüşümü
- [x] 4 SQLite tablosu: income_statement, balance_sheet, cash_flow, ratios
- [x] CLI hybrid RAG testi — SQL + Vector birlikte çalışıyor

**Geçiş kriteri:** Türkçe sayısal sorulara SQL üzerinden doğru, kaynaklı cevap geliyor. ✅

---

## FAZ 3 — LangGraph Agent + FastAPI + React Frontend ✅
**Hedef:** Agentic RAG sistemi + web arayüzü.

- [x] `state.py` — AgentState tanımı (question, ticker, sub_tasks, retrieved, ...)
- [x] `planner_node.py` — Claude Haiku ile soruyu alt görevlere böl
- [x] `router_node.py` — asyncio.gather ile paralel retriever çağrısı + duplicate önleme
- [x] `critic_node.py` — bilgi yeterli mi? SUFFICIENT / INSUFFICIENT
- [x] `synthesizer_node.py` — Claude Sonnet ile kaynaklı Türkçe yanıt (max 12 kaynak)
- [x] `graph.py` — LangGraph StateGraph (Planner → Router → Critic → Synthesizer, max 3 retry)
- [x] FastAPI backend — upload, ask, fetch-data, health endpoint'leri
- [x] PDF pipeline — pdfplumber (tablolar) + PyMuPDF (metin) + yfinance güncelleme
- [x] React frontend — Sidebar, ChatPage, ChatInput, Message, ThinkingIndicator
- [x] Sohbet hafızası (localStorage + API conversation_history)
- [x] LangSmith tracing entegrasyonu
- [x] BIST-30 tam destek

**Geçiş kriteri:** Uçtan uca çalışan, kaynaklı Türkçe cevap veren platform. ✅

---

## FAZ 3.5 — Temettü Verisi, Auto-Fetch, Haber Retriever ✅
**Hedef:** Agent'ın veri kapsamını genişlet.

- [x] `dividends` tablosu — yfinance .dividends ile temettü verisi
- [x] Temettü verimi hesaplama — dividends JOIN ratios.current_price
- [x] Auto-fetch — SQL boş dönünce otomatik yfinance'den çekip tekrar sorgulama
- [x] News retriever — RSS haber arama (Bloomberg HT, Dünya gazetesi)
- [x] 504 sayfalık TUPRS raporu ile performans testi — başarılı

**Geçiş kriteri:** Temettü, haber ve auto-fetch çalışıyor, büyük raporlarda performans iyi. ✅

---

## FAZ 4 — Çoklu Şirket Karşılaştırma ✅
**Hedef:** 2 hisseyi yan yana karşılaştırma.

- [x] `compare.py` — GET /api/compare/metrics + POST /api/compare/ask endpoint'leri
- [x] Multi-ticker agent desteği — per-task ticker, PLANNER_PROMPT_MULTI, SYSTEM_PROMPT_COMPARE
- [x] React Router — `/` (sohbet) ve `/compare` (karşılaştırma) sayfaları
- [x] TickerSelector — Multi-select (2 ticker, badge + dropdown)
- [x] ComparisonTable — 12 metrik satırı, formatlanmış büyük sayılar
- [x] ComparisonChat — Karşılaştırma Q&A (ephemeral)
- [x] Sidebar navigasyonu — Sohbet / Karşılaştır sekmeli geçiş
- [x] Shared constants — BIST_TICKERS tek kaynak (`constants/tickers.ts`)
- [x] Router task timeout (30s) + Qdrant timeout (15s)

**Geçiş kriteri:** 2 hisseyi metrik tablosu + AI chat ile karşılaştırabilme. ✅

---

## FAZ 5 — Firebase Auth + Landing Page ✅
**Hedef:** Kullanıcı kimlik doğrulama ve profesyonel landing page.

- [x] Firebase projesi kurulumu + GoogleAuthProvider
- [x] `config/firebase.ts` — Firebase config + auth export
- [x] `contexts/AuthContext.tsx` — signInWithGoogle, signOut, useAuth hook
- [x] `main.tsx` — AuthProvider + BrowserRouter sarma
- [x] `App.tsx` — Auth guard: `!user` → LoginPage, `user` → Layout shell
- [x] `backend/auth.py` — Backend auth middleware (Firebase token doğrulama)
- [x] Backend route'larına auth koruması eklendi
- [x] Landing Page (LoginPage.tsx) tam yeniden tasarım — 9 bölüm:
  - Navbar (frosted glass, logo + CTA butonları)
  - Hero Section (min-h-screen, 2 sütun, inline SVG chat mockup, gradient bloblar)
  - Trust Strip (4 metrik ikon+text)
  - Nasıl Çalışır? (3 adım, dashed connector, numaralı ikonlar)
  - Özellikler (6 renkli kart, lg:grid-cols-3)
  - Platform Önizleme (browser frame SVG mockup + bullet points)
  - FAQ Accordion (5 soru, useState toggle, chevron animasyonu)
  - Final CTA (bg-gray-900 koyu banner)
  - Footer (3 sütun + © 2026 alt bar)
- [x] Tüm görseller inline SVG + CSS (harici imaj yok)
- [x] Responsive: mobil/tablet/desktop
- [x] TypeScript hatasız (`npx tsc --noEmit`)

**Geçiş kriteri:** Google ile giriş yapılabiliyor, giriş yapmayanlar profesyonel landing page görüyor. ✅

---

## FAZ 6 — Deployment + Ürünleştirme
**Hedef:** Canlıya alma ve ilk kullanıcılar.

- [ ] Railway deployment (backend, FastAPI + Uvicorn)
- [ ] Vercel deployment (frontend, React + Vite)
- [ ] Environment variables production konfigürasyonu
- [ ] CORS güncelleme (production domain'leri)
- [ ] Custom domain bağlama (agentick.io)

**Geçiş kriteri:** app.agentick.io üzerinden gerçek kullanıcılar erişebiliyor.

---

## FAZ 7 — Kullanıcı Kotası + Stripe
**Hedef:** Freemium iş modeli.

- [ ] Firestore ile kullanıcı başına sorgu sayacı
- [ ] Aylık 5 ücretsiz sorgu limiti
- [ ] Limit aşımında ödeme sayfasına yönlendirme
- [ ] Stripe Payment Link — Pro abonelik (₺199/ay)

**Geçiş kriteri:** Kullanıcı 5 ücretsiz sorgu kullanabiliyor, 6.'da ödeme sayfasına yönleniyor.

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
- [ ] LangSmith ile LLM gözlemlenebilirlik aktif
- [ ] Railway + Vercel deployment canlı
- [ ] Reddit r/Borsasi paylaşımı
- [ ] Twitter/X `#BIST` paylaşımı
- [ ] İlk 50 kullanıcı → feedback döngüsü başladı
