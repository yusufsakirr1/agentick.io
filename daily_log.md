# agentick.io — Daily Log

Günlük çalışma kaydı. Her oturumun sonunda güncellenir ve commit edilir.

---

## 2026-07-17

### Yapılanlar
- README.md sıfırdan yazıldı (proje tanımı, mimari diagram, stack tablosu, kurulum, faz durumları)
- Proje için ayrı git reposu başlatıldı (`git init` — daha önce üst dizin reposuna gitignore'lanmıştı)
- GitHub reposu açıldı: `github.com/yusufsakirr1/agentick.io`
- İlk commit ve push tamamlandı (17 dosya, Faz 1 kodunun tamamı dahil)
- `yfinance` bağımlılığı eklendi (`uv add yfinance`)
- BIST ticker formatı doğrulandı: `THYAO.IS` → 329.50 TRY

### Notlar
- yfinance'de BIST hisseleri `.IS` suffix olmadan bulunamıyor (`THYAO` değil `THYAO.IS`)

---

## [Faz 1 — Tamamlanan Önceki Oturumlar]

### Yapılanlar
- `uv` ile proje iskeleti kuruldu (`pyproject.toml`, `.env`, `.gitignore`, `.python-version`)
- THYAO Mart 2026 YK Faaliyet Raporu KAP'tan manuel indirildi (API bot engeli nedeniyle)
- `kap_client.py`: KAP PDF doğrulama scripti yazıldı
- `pdf_chunker.py`: Türkçe PDF → 27 chunk (25 sayfa, ~500-800 token/chunk, %10 overlap)
- `build_vector_index.py`: `paraphrase-multilingual-mpnet-base-v2` ile 768 boyutlu embedding üretildi, Qdrant Cloud Frankfurt cluster'a yüklendi
- `vector_retriever.py`: Qdrant semantic search, ticker filtreli sorgular
- `cli_test.py`: Uçtan uca test — "THY'nin 2026 finansal sonuçları?" sorusuna Türkçe cevap alındı
- `mimari.md`, `roadmap.md`, `dokuman.md` oluşturuldu

### Çözülen Sorunlar
| Sorun | Çözüm |
|---|---|
| KAP API 666 status kodu (bot engeli) | PDF elle indirildi |
| KAP PDF'leri Java wrapper'ına sarılı | `%PDF` byte offsetinden itibaren kes |
| Voyage AI ücretsiz tier kısıtlı | Yerel `paraphrase-multilingual-mpnet-base-v2` kullanıldı |
| Qdrant 1.16.1'de `search()` kaldırıldı | `query_points()` ile değiştirildi |
| Qdrant ticker filtresi hata veriyordu | `create_payload_index()` eklendi |
| Groq API key geçersiz geldi | Ollama (llama3.2 lokal) ile devam edildi |
| `.python-version` 3.12, pyenv'de 3.11.9 vardı | `uv python pin 3.12` ile çözüldü |

### Faz 1 Çıktı Kriteri ✅
Tek kaynaklı Türkçe sorulara doğru, kaynaklı cevap geliyor.

---

## Sıradaki (Faz 2 — SQL Retriever)

- [ ] `bist_finance_client.py` — `yfinance` ile THYAO.IS gelir tablosu, bilanço, oranlar çekme
- [ ] `sql_retriever.py` — text-to-SQL: Türkçe soru → SQL → sayısal sonuç
- [ ] SQLite'a veri yazma ve sorgulama testi
- [ ] Çıktı kriteri: "THYAO'nun son 3 yılın net marjı nedir?" sorusuna sayısal, kaynaklı cevap
