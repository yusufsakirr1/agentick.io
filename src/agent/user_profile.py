"""
Kullanıcı profili — cevabın vurgusunu kişiselleştirir.

Profil ASLA yatırım tavsiyesi üretmez. Yalnızca iki şeyi belirler:
  1. Hangi metriklerin öne çıkarılacağı (risk profili, vade, odak alanları)
  2. Dilin ne kadar teknik olacağı (deneyim seviyesi)

SPK uyumluluk kuralları profilden bağımsız olarak her durumda geçerlidir —
`build_profile_directive` çıktısı system prompt'un SONUNA değil, uyumluluk
bloğundan ÖNCE eklenir ki son söz her zaman uyumluluk kurallarında kalsın.

Değerler istemciden geldiği için `sanitize_profile` ile beyaz listeye
sokulur; bilinmeyen anahtar veya değer sessizce atılır.
"""

RISK_PROFILES = {
    "temkinli": (
        "Kullanıcı temkinli bir yaklaşımı tercih ediyor: borçluluk, likidite ve "
        "nakit akışı göstergelerini öne çıkar, risk faktörlerini açıkça belirt."
    ),
    "dengeli": (
        "Kullanıcı dengeli bir yaklaşımı tercih ediyor: büyüme ve risk "
        "göstergelerini birlikte, eşit ağırlıkta sun."
    ),
    "agresif": (
        "Kullanıcı büyüme odaklı bir yaklaşımı tercih ediyor: büyüme oranları, "
        "marj genişlemesi ve yatırım harcamalarını öne çıkar; riskleri yine de eksiksiz belirt."
    ),
}

HORIZONS = {
    "kisa": (
        "Yatırım vadesi kısa (1 yıldan az): en güncel çeyreklik verilere ve "
        "son gelişmelere ağırlık ver."
    ),
    "orta": (
        "Yatırım vadesi orta (1-3 yıl): son 2-3 yıllık trendlere ağırlık ver."
    ),
    "uzun": (
        "Yatırım vadesi uzun (3 yıldan fazla): çok yıllık trendlere, "
        "sürdürülebilirlik ve yapısal göstergelere ağırlık ver."
    ),
}

FOCUS_AREAS = {
    "temettu": "temettü geçmişi, temettü verimi ve dağıtım oranı",
    "buyume": "gelir ve net kâr büyüme oranları",
    "deger": "F/K, PD/DD gibi değerleme çarpanları",
    "likidite": "cari oran, nakit pozisyonu ve borç çevirme kapasitesi",
}

EXPERIENCE_LEVELS = {
    "baslangic": (
        "Kullanıcı finansal terimlere yeni: her teknik terimi ilk geçtiğinde "
        "parantez içinde tek cümleyle açıkla."
    ),
    "orta": "",
    "ileri": (
        "Kullanıcı finansal terimlere hakim: terimleri açıklamadan kullan, "
        "doğrudan verilere gir."
    ),
}

MAX_FOCUS_AREAS = 4


def sanitize_profile(raw: dict | None) -> dict:
    """
    İstemciden gelen profili beyaz listeye indirger.

    Bilinmeyen anahtar/değerler atılır; hiçbir geçerli alan kalmazsa boş sözlük döner.
    """
    if not isinstance(raw, dict):
        return {}

    clean: dict = {}

    risk = raw.get("riskProfile")
    if risk in RISK_PROFILES:
        clean["riskProfile"] = risk

    horizon = raw.get("horizon")
    if horizon in HORIZONS:
        clean["horizon"] = horizon

    experience = raw.get("experience")
    if experience in EXPERIENCE_LEVELS:
        clean["experience"] = experience

    focus = raw.get("focus")
    if isinstance(focus, list):
        # Sırayı koru, tekrarları at, üst sınırı uygula
        seen = []
        for f in focus:
            if f in FOCUS_AREAS and f not in seen:
                seen.append(f)
        if seen:
            clean["focus"] = seen[:MAX_FOCUS_AREAS]

    return clean


def build_profile_directive(raw: dict | None) -> str:
    """
    Profili system prompt'a eklenecek talimat bloğuna çevirir.

    Profil boşsa boş string döner — bu durumda prompt hiç değişmez.
    """
    profile = sanitize_profile(raw)
    if not profile:
        return ""

    lines = []

    if risk := profile.get("riskProfile"):
        lines.append(f"- {RISK_PROFILES[risk]}")

    if horizon := profile.get("horizon"):
        lines.append(f"- {HORIZONS[horizon]}")

    if focus := profile.get("focus"):
        areas = ", ".join(FOCUS_AREAS[f] for f in focus)
        lines.append(
            f"- Kullanıcının özellikle ilgilendiği konular: {areas}. "
            "Veri varsa bunlara öncelik ver."
        )

    if experience := profile.get("experience"):
        if text := EXPERIENCE_LEVELS[experience]:
            lines.append(f"- {text}")

    if not lines:
        return ""

    return (
        "\n\nKullanıcı tercihleri (yalnızca VURGU ve DİL için — tavsiye üretme aracı değil):\n"
        + "\n".join(lines)
        + "\n- Bu tercihler hangi verinin öne çıkacağını belirler; asla bir alım-satım "
        "yönlendirmesine, uygunluk değerlendirmesine veya 'bu profile uygun/uygun değil' "
        "türü bir yoruma dönüştürülemez.\n"
        "- Veri yoksa tercihleri karşılamak için tahmin yapma."
    )


def apply_profile(system_prompt: str, raw: dict | None) -> str:
    """
    Profil talimatını system prompt'a, uyumluluk bloğundan ÖNCE yerleştirir.

    Böylece SPK kuralları prompt'un son bölümü olarak kalır ve profil onları
    gölgeleyemez.
    """
    directive = build_profile_directive(raw)
    if not directive:
        return system_prompt

    marker = "Yasal uyumluluk kuralları"
    idx = system_prompt.find(marker)
    if idx == -1:
        return system_prompt + directive

    return system_prompt[:idx].rstrip() + directive + "\n\n" + system_prompt[idx:]
