import streamlit as st
import json
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_MEVCUT = True
except ImportError:
    ANTHROPIC_MEVCUT = False

# ==========================================
# 0. SAYFA AYARLARI
# ==========================================
st.set_page_config(
    page_title="TYMM 11. Sınıf Tarih Soru Üreteci",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. MÜFREDAT VERİ YAPISI (TYMM 11. SINIF TARİH)
# ==========================================
MUFREDAT_11_SINIF = {
    "1. ÜNİTE: 1683-1789 Arasında Osmanlı Devleti ve Dünya": {
        "kavramlar": ["Barok", "Devrim", "Hendesehane", "Matbaa", "Rokoko", "Sanayileşme", "Sefaret"],
        "beceriler": [
            "SBAB1. Zamanı Algılama ve Kronolojik Düşünme",
            "SBAB2. Kanıta Dayalı Sorgulama ve Araştırma",
            "SBAB4. Değişim ve Sürekliliği Algılama"
        ],
        "kazanimlar": {
            "TAR.11.1.1": "Osmanlı Devleti'nin 1683-1789 yılları arasındaki siyasi ve askerî mücadelelerini sonuçları açısından değerlendirebilme (Karşılaştırma ve yargıda bulunma).",
            "TAR.11.1.2": "Lale Devri'nde Osmanlı devlet ve toplum hayatında meydana gelen değişimi tarihsel bağlamı içerisinde yorumlayabilme (Kaynak inceleme, tablolaştırma, açıklama).",
            "TAR.11.1.3": "1755 Lizbon ve 1766 İstanbul depremlerini ortaya çıkardığı etkiler bakımından karşılaştırabilme (Benzerlik ve farklılıkları listeleme).",
            "TAR.11.1.4": "Sanayi Devrimi'nin meydana getirdiği siyasi, sosyal ve ekonomik değişimi neden ve sonuçlarıyla birlikte yorumlayabilme (Olumlu/olumsuz yönleri sorgulama)."
        }
    },
    "2. ÜNİTE: Değişim Çağında Osmanlı Devleti ve Dünya (1789-1908)": {
        "kavramlar": [
            "Azınlık", "Cumhuriyetçilik", "İhtilal", "Kapitalizm", "Komünizm",
            "Liberalizm", "Meşrutiyet", "Milliyetçilik", "Panslavizm", "Sosyalizm"
        ],
        "beceriler": [
            "SBAB4. Değişim ve Sürekliliği Algılama",
            "SBAB2. Kanıta Dayalı Sorgulama",
            "SBAB17. Tarihsel Sorun Analizi ve Karar Verme"
        ],
        "kazanimlar": {
            "TAR.11.2.1": "Fransız İhtilali'nin devlet ve toplum hayatında meydana getirdiği değişimi neden ve sonuçlarıyla yorumlayabilme.",
            "TAR.11.2.2": "1789-1908 yılları arasında meydana gelen siyasi, askerî ve idari gelişmelerin Osmanlı Devleti'nin yönetim ve toplum yapısına etkilerini sorgulayabilme.",
            "TAR.11.2.3": "1789-1908 yılları arasında Osmanlı Devleti'nde bilim, sanat ve teknoloji alanlarında yapılan uygulamaları yorumlayabilme.",
            "TAR.11.2.4": "Osmanlı Devleti'nin sanayileşmede geri kalmasına neden olan etmenleri ortadan kaldırmaya yönelik alternatif fikirler üretebilme (Tarihsel Sorun Analizi)."
        }
    },
    "3. ÜNİTE: Savaşlar Sarmalında Osmanlı (1908-1918)": {
        "kavramlar": ["Bloklaşma", "Darbe", "Fırka", "Göç", "Komita", "Muhacir", "Mütareke", "Müttefik", "Salgın"],
        "beceriler": [
            "SBAB3. Tarihsel Empati (Tarihsel Bağlamsallaştırma)",
            "SBAB2. Kanıta Dayalı Sorgulama ve Araştırma"
        ],
        "kazanimlar": {
            "TAR.11.3.1": "1908-1918 yılları arasında Osmanlı Devleti'nde meydana gelen siyasi ve askerî gelişmelerin sonuçlarını tarihsel bağlamı içerisinde değerlendirebilme.",
            "TAR.11.3.2": "1908-1918 yılları arasında yaşanan kitlesel göç ve salgınların Osmanlı devlet ve toplum hayatına etkilerine ilişkin bakış açısı geliştirebilme (Tarihsel Empati).",
            "TAR.11.3.3": "Osmanlı Devleti'nin insanlık tarihine katkılarına ilişkin oluşturduğu özgün ürünleri paylaşabilme."
        }
    }
}

SORU_TIPLERI = [
    "Bağlam Temelli Çoktan Seçmeli (%40 TYMM)",
    "ÖSYM Tarzı Klasik / Bilişsel (%60)",
    "Açık Uçlu Senaryo / Analiz Sorusu",
    "Eşleştirme Sorusu",
    "Doğru/Yanlış + Gerekçelendirme"
]

ZORLUK_SECENEKLERI = ["Kolay", "Orta", "Zor (ÖSYM Üst Seviye)", "Derecelendirilmiş / Şampiyon"]

# ==========================================
# 2. YARDIMCI FONKSİYONLAR
# ==========================================

def init_session_state():
    """Oturum durumunu (geçmiş, favoriler, üretilen soru) başlatır."""
    if "gecmis" not in st.session_state:
        st.session_state.gecmis = []
    if "favoriler" not in st.session_state:
        st.session_state.favoriler = []
    if "uretilen_soru" not in st.session_state:
        st.session_state.uretilen_soru = None


def soru_uret_api(api_key, model, prompt):
    """Anthropic API'sini çağırarak promptu doğrudan bir soruya dönüştürür."""
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    parcalar = [blok.text for blok in response.content if blok.type == "text"]
    return "\n".join(parcalar)


def build_prompt(unite_adi, kazanim_kodu, kazanim_tanimi, soru_tipi, zorluk,
                  odak_kavramlar, ek_baglam, soru_sayisi):
    """Seçilen parametrelere göre LLM'e gönderilecek promptu oluşturur."""
    tum_kavramlar = MUFREDAT_11_SINIF[unite_adi]["kavramlar"]
    beceriler = ", ".join(MUFREDAT_11_SINIF[unite_adi]["beceriler"])

    # Kullanıcı belirli kavramlar seçtiyse onları, seçmediyse tüm kavramları kullan
    kavramlar = ", ".join(odak_kavramlar) if odak_kavramlar else ", ".join(tum_kavramlar)

    coktan_secmeli_blok = """
3. **Seçenekler ve Çözüm (Çoktan Seçmeli ise):**
   - A, B, C, D, E olmak üzere 5 seçenek içermelidir. Çeldiriciler güçlü ve mantıklı olmalıdır.
   - Doğru cevap açıkça belirtilmeli ve detaylı pedagojik "Çözüm Açıklaması" eklenmelidir.
"""

    acik_uclu_blok = """
4. **Klasik / Açık Uçlu ise:**
   - Öğrencinin üst düzey düşünme becerisini ortaya koyacak yönlendirici soru maddeleri olmalı.
   - Detaylı ve puanlama kriterlerini içeren bir "Dereceli Puanlama Anahtarı (Rubrik)" eklenmelidir.
"""

    baglam_temelli_mi = "Bağlam Temelli" in soru_tipi
    baglam_soru_sayisi = max(soru_sayisi, 2) if baglam_temelli_mi else soru_sayisi

    baglam_temelli_blok = """
5. **Bağlam Temelli Soru Kurgusu (ÖSYM / TYMM Mantığı — ZORUNLU):**
   - Önce TEK, uzun ve zengin bir bağlam metni (öncül) yazılmalıdır. Bu metin en az 120-180 kelime uzunluğunda olmalı; birden fazla cümle/paragraftan oluşan, ayrıntılı bir arşiv belgesi alıntısı, seyahatname parçası, tarihçi değerlendirmesi, karşılaştırmalı tablo/kronoloji anlatımı ya da özgün olay anlatımı şeklinde kurgulanmalıdır. Metin; kişi, yer, tarih, sebep-sonuç ilişkisi gibi somut ayrıntılar içermeli, öğrencinin metni dikkatle okuyup çıkarım yapmasını gerektirecek yoğunlukta olmalıdır.
   - Bu TEK bağlam metnine dayanan EN AZ 2 (iki) farklı soru üretilmelidir (gerçek ÖSYM sınavlarındaki "Bu parçaya göre..." mantığıyla aynı paragrafa bağlı ardışık sorular gibi).
   - Bağlama bağlı sorular birbirinin aynısı olmamalı; her biri kazanımın farklı bir boyutunu (ör. biri doğrudan bilgi/çıkarım, diğeri neden-sonuç ilişkisi, bir diğeri karşılaştırma veya yargıya ulaşma/ulaşamama) ölçmelidir.
   - Bağlam metni yalnızca bir kez, sorular grubunun en başında verilmeli; her soru öncesinde tekrarlanmamalı, sorular metnin altında "1.", "2." şeklinde sıralanmalıdır.
   - Her bağlam temelli soru da 5 seçenekli (A-E) olmalı, güçlü çeldiricilerle ve ayrıntılı "Çözüm Açıklaması" ile desteklenmelidir.
"""

    prompt = f"""Sen Türkiye Yüzyılı Maarif Modeli (TYMM) standartlarına hakim, ÖSYM tarzında üst düzey bilişsel ölçme değerlendirme soruları hazırlayan uzman bir Tarih soru yazarısın.

Aşağıdaki parametreler doğrultusunda {"aynı bağlam metnine dayanan EN AZ " + str(baglam_soru_sayisi) + " adet" if baglam_temelli_mi else str(soru_sayisi) + " adet"} nitelikli 11. Sınıf Tarih sorusu oluştur:

---
### 📋 SORU PARAMETRELERİ
- **Ders:** Tarih (11. Sınıf)
- **Ünite / Tema:** {unite_adi}
- **Öğrenme Çıktısı (Kazanım):** {kazanim_kodu} - {kazanim_tanimi}
- **İlgili Alan Becerileri:** {beceriler}
- **Anahtar Kavramlar:** {kavramlar}
- **Soru Tipi:** {soru_tipi}
- **Zorluk / Bilişsel Düzey:** {zorluk}
- **Üretilecek Soru Sayısı:** {baglam_soru_sayisi if baglam_temelli_mi else soru_sayisi}
{"- **Özel Bağlam / Metin Notu:** " + ek_baglam if ek_baglam else ""}
---

### ✍️ SORU YAZIM KURALLARI VE BİÇİMLENDİRME:
1. **Bağlam Metni (Öncül):**
   - Sorunun başında mutlaka tarihsel bir bağlam (birinci elden arşiv belgesi, seyahatname alıntısı, tarihçi görüşü, karşılaştırma tablosu veya tarihsel olay özeti) yer almalıdır.
   - Metin özgün, tarihsel gerçekliklere sadık ve edebi dili güçlü olmalıdır.

2. **Soru Kökü:**
   - Kazanımda hedeflenen beceriyi (analiz, çıkarım, tarihsel empati, karşılaştırma vb.) doğrudan ölçmelidir.
   - "...yargılardan hangisine ulaşılabilir / ulaşılamaz?" veya "...aşağıdakilerden hangisi gösterilebilir / gösterilemez?" şeklinde net olmalıdır.
{coktan_secmeli_blok if "Çoktan Seçmeli" in soru_tipi or "ÖSYM" in soru_tipi else ""}{acik_uclu_blok if "Açık Uçlu" in soru_tipi or "Klasik" in soru_tipi else ""}{baglam_temelli_blok if baglam_temelli_mi else ""}
6. **Genel Kalite Kriterleri:**
   - Sorular birbirini tekrar etmemeli, her biri farklı bir alt beceriyi veya bakış açısını ölçmelidir.
   - Tarihsel doğruluk esastır; kurgusal ama tarihe sadık bağlam metinleri kullanılabilir.

Lütfen çıktıyı şık ve okunaklı bir Markdown formatında, her soruyu numaralandırarak sun.
"""
    return prompt


def gecmise_ekle(unite_adi, kazanim_kodu, soru_tipi, zorluk, prompt):
    """Üretilen promptu oturum geçmişine kaydeder (en fazla 20 kayıt)."""
    kayit = {
        "zaman": datetime.now().strftime("%H:%M:%S"),
        "unite": unite_adi,
        "kazanim": kazanim_kodu,
        "soru_tipi": soru_tipi,
        "zorluk": zorluk,
        "prompt": prompt,
    }
    st.session_state.gecmis.insert(0, kayit)
    st.session_state.gecmis = st.session_state.gecmis[:20]


# ==========================================
# 3. ANA UYGULAMA
# ==========================================
init_session_state()

st.title("🏛️ TYMM 11. Sınıf Tarih Soru Üreteci")
st.markdown("**Türkiye Yüzyılı Maarif Modeli** ve **ÖSYM** standartlarında bağlam temelli soru ve materyal hazırlama aracı.")
st.divider()

# ---- Sidebar: Parametre Seçimleri ----
with st.sidebar:
    st.header("⚙️ Müfredat Seçimleri")

    unite_secimi = st.selectbox(
        "1. Ünite / Tema Seçiniz:",
        options=list(MUFREDAT_11_SINIF.keys())
    )

    kazanimlar_dict = MUFREDAT_11_SINIF[unite_secimi]["kazanimlar"]
    kazanim_kodu = st.selectbox(
        "2. Öğrenme Çıktısı (Kazanım):",
        options=list(kazanimlar_dict.keys()),
        format_func=lambda x: f"{x} - {kazanimlar_dict[x][:45]}..."
    )
    kazanim_tanimi = kazanimlar_dict[kazanim_kodu]

    st.divider()
    st.header("🎯 Soru Formatı")

    soru_tipi = st.radio("Soru Tipi:", SORU_TIPLERI)

    zorluk = st.select_slider("Zorluk Derecesi:", options=ZORLUK_SECENEKLERI)

    soru_sayisi = st.number_input(
        "Üretilecek Soru Sayısı:",
        min_value=1, max_value=10, value=1, step=1,
        help="Bağlam Temelli seçiliyse, aynı bağlama dayalı en az 2 soru otomatik olarak istenir."
    )
    if "Bağlam Temelli" in soru_tipi and soru_sayisi < 2:
        st.caption("ℹ️ Bağlam temelli sorularda ÖSYM/TYMM mantığı gereği aynı metne dayalı en az 2 soru istenecektir.")

    st.divider()
    st.header("🏷️ Odak Kavramlar (İsteğe Bağlı)")
    odak_kavramlar = st.multiselect(
        "Soruda özellikle vurgulanmasını istediğiniz kavramları seçin:",
        options=MUFREDAT_11_SINIF[unite_secimi]["kavramlar"]
    )

    st.divider()
    st.header("🤖 AI ile Doğrudan Üretim")
    if not ANTHROPIC_MEVCUT:
        st.warning("`anthropic` paketi kurulu değil. Kurmak için: `pip install anthropic`")
    api_key = st.text_input(
        "Anthropic API Anahtarı:",
        type="password",
        help="Anahtarınız yalnızca bu oturumda kullanılır, hiçbir yerde saklanmaz."
    )
    model_secimi = st.selectbox(
        "Model:",
        options=["claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"],
        index=0,
        help="Güncel model listesi Anthropic tarafından değişebilir; gerekirse buradaki değerleri güncelleyin."
    )

# ---- Ana Ekran ----
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📌 Seçili Kazanım ve Detaylar")
    st.info(f"**Kazanım Kodu:** {kazanim_kodu}\n\n**Açıklama:** {kazanim_tanimi}")

    st.subheader("📝 Özel Bağlam Notu / Metin Girin (İsteğe Bağlı)")
    ek_baglam = st.text_area(
        "Soru kurgusunda geçmesini istediğiniz özel tarihçi ismi, arşiv belgesi veya olayı yazabilirsiniz:",
        placeholder="Örn: Rami Mehmed Efendi ile Count Öttingen arasındaki Karlofça müzakeresi metni kullanılsın...",
        height=100
    )

with col2:
    st.subheader("🏷️ Ünite Anahtar Öğeleri")
    st.write("**Kavramlar:**")
    st.write(", ".join([f"`{k}`" for k in MUFREDAT_11_SINIF[unite_secimi]["kavramlar"]]))

    st.write("**Öne Çıkan Beceriler:**")
    for b in MUFREDAT_11_SINIF[unite_secimi]["beceriler"]:
        st.caption(f"• {b}")

st.divider()

# ---- Prompt Üretme ve Gösterim Alanı ----
st.subheader("🚀 Yapay Zeka Soru Üretim Promptu")

generated_prompt = build_prompt(
    unite_secimi, kazanim_kodu, kazanim_tanimi, soru_tipi, zorluk,
    odak_kavramlar, ek_baglam, soru_sayisi
)

st.text_area(
    "Aşağıdaki promptu LLM (Claude, ChatGPT, Gemini) modeline yapıştırarak sorunuzu üretebilirsiniz:",
    value=generated_prompt,
    height=320,
    key="prompt_output"
)

col_btn0, col_btn1, col_btn2, col_btn3 = st.columns(4)

with col_btn0:
    uret_tiklandi = st.button(
        "✨ Soruyu Şimdi Üret",
        use_container_width=True,
        type="primary",
        disabled=not ANTHROPIC_MEVCUT
    )

with col_btn1:
    if st.button("💾 Promptu Geçmişe Kaydet", use_container_width=True):
        gecmise_ekle(unite_secimi, kazanim_kodu, soru_tipi, zorluk, generated_prompt)
        st.success("Geçmişe kaydedildi!")

with col_btn2:
    st.download_button(
        label="⬇️ Prompt Olarak İndir (.txt)",
        data=generated_prompt,
        file_name=f"tarih_soru_prompt_{kazanim_kodu}.txt",
        mime="text/plain",
        use_container_width=True
    )

with col_btn3:
    disa_aktarim = {
        "unite": unite_secimi,
        "kazanim_kodu": kazanim_kodu,
        "kazanim_tanimi": kazanim_tanimi,
        "soru_tipi": soru_tipi,
        "zorluk": zorluk,
        "soru_sayisi": soru_sayisi,
        "odak_kavramlar": odak_kavramlar,
        "ek_baglam": ek_baglam,
        "prompt": generated_prompt
    }
    st.download_button(
        label="⬇️ JSON Olarak İndir",
        data=json.dumps(disa_aktarim, ensure_ascii=False, indent=2),
        file_name=f"tarih_soru_config_{kazanim_kodu}.json",
        mime="application/json",
        use_container_width=True
    )

st.success("✅ Prompt başarıyla kurgulandı! Yukarıdaki metni kopyalayıp doğrudan modelinize gönderebilirsiniz.")

# ---- Doğrudan AI Üretimi ----
if uret_tiklandi:
    if not ANTHROPIC_MEVCUT:
        st.error("`anthropic` paketi kurulu değil. Terminalde `pip install anthropic` çalıştırıp uygulamayı yeniden başlatın.")
    elif not api_key:
        st.error("Lütfen sol menüden Anthropic API anahtarınızı girin.")
    else:
        with st.spinner("Soru üretiliyor, lütfen bekleyin..."):
            try:
                st.session_state.uretilen_soru = soru_uret_api(api_key, model_secimi, generated_prompt)
            except anthropic.AuthenticationError:
                st.error("API anahtarı geçersiz görünüyor. Lütfen kontrol edip tekrar deneyin.")
            except anthropic.APIStatusError as e:
                st.error(f"API hatası: {e}")
            except Exception as e:
                st.error(f"Beklenmeyen bir hata oluştu: {e}")

if st.session_state.uretilen_soru:
    st.divider()
    st.subheader("📄 Üretilen Soru")
    st.markdown(st.session_state.uretilen_soru)
    st.download_button(
        label="⬇️ Üretilen Soruyu İndir (.md)",
        data=st.session_state.uretilen_soru,
        file_name=f"tarih_soru_{kazanim_kodu}.md",
        mime="text/markdown"
    )

# ---- Geçmiş Kayıtlar ----
if st.session_state.gecmis:
    st.divider()
    with st.expander(f"🕓 Geçmiş Kayıtlar ({len(st.session_state.gecmis)})", expanded=False):
        for i, kayit in enumerate(st.session_state.gecmis):
            st.markdown(
                f"**{kayit['zaman']}** — {kayit['unite'][:35]}... "
                f"| `{kayit['kazanim']}` | {kayit['soru_tipi']} | {kayit['zorluk']}"
            )
            with st.popover(f"Görüntüle #{i+1}"):
                st.text_area("Prompt", value=kayit["prompt"], height=200, key=f"gecmis_{i}")
