import streamlit as st

# Set Streamlit Page Configuration
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
            "TAR.11.1.1": "Osmanlı Devleti’nin 1683-1789 yılları arasındaki siyasi ve askerî mücadelelerini sonuçları açısından değerlendirebilme (Karşılaştırma ve yargıda bulunma).",
            "TAR.11.1.2": "Lale Devri’nde Osmanlı devlet ve toplum hayatında meydana gelen değişimi tarihsel bağlamı içerisinde yorumlayabilme (Kaynak inceleme, tablolaştırma, açıklama).",
            "TAR.11.1.3": "1755 Lizbon ve 1766 İstanbul depremlerini ortaya çıkardığı etkiler bakımından karşılaştırabilme (Benzerlik ve farklılıkları listeleme).",
            "TAR.11.1.4": "Sanayi Devrimi’nin meydana getirdiği siyasi, sosyal ve ekonomik değişimi neden ve sonuçlarıyla birlikte yorumlayabilme (Olumlu/olumsuz yönleri sorgulama)."
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
            "TAR.11.2.1": "Fransız İhtilali’nin devlet ve toplum hayatında meydana getirdiği değişimi neden ve sonuçlarıyla yorumlayabilme.",
            "TAR.11.2.2": "1789-1908 yılları arasında meydana gelen siyasi, askerî ve idari gelişmelerin Osmanlı Devleti’nin yönetim ve toplum yapısına etkilerini sorgulayabilme.",
            "TAR.11.2.3": "1789-1908 yılları arasında Osmanlı Devleti’nde bilim, sanat ve teknoloji alanlarında yapılan uygulamaları yorumlayabilme.",
            "TAR.11.2.4": "Osmanlı Devleti’nin sanayileşmede geri kalmasına neden olan etmenleri ortadan kaldırmaya yönelik alternatif fikirler üretebilme (Tarihsel Sorun Analizi)."
        }
    },
    "3. ÜNİTE: Savaşlar Sarmalında Osmanlı (1908-1918)": {
        "kavramlar": ["Bloklaşma", "Darbe", "Fırka", "Göç", "Komita", "Muhacir", "Mütareke", "Müttefik", "Salgın"],
        "beceriler": [
            "SBAB3. Tarihsel Empati (Tarihsel Bağlamsallaştırma)",
            "SBAB2. Kanıta Dayalı Sorgulama ve Araştırma"
        ],
        "kazanimlar": {
            "TAR.11.3.1": "1908-1918 yılları arasında Osmanlı Devleti’nde meydana gelen siyasi ve askerî gelişmelerin sonuçlarını tarihsel bağlamı içerisinde değerlendirebilme.",
            "TAR.11.3.2": "1908-1918 yılları arasında yaşanan kitlesel göç ve salgınların Osmanlı devlet ve toplum hayatına etkilerine ilişkin bakış açısı geliştirebilme (Tarihsel Empati).",
            "TAR.11.3.3": "Osmanlı Devleti’nin insanlık tarihine katkılarına ilişkin oluşturduğu özgün ürünleri paylaşabilme."
        }
    }
}

# ==========================================
# 2. PROMPT OLUŞTURUCU FONKSİYON
# ==========================================
def build_prompt(unite_adi, kazanim_kodu, kazanim_tanimi, soru_tipi, zorluk, ek_baglam):
    kavramlar = ", ".join(MUFREDAT_11_SINIF[unite_adi]["kavramlar"])
    beceriler = ", ".join(MUFREDAT_11_SINIF[unite_adi]["beceriler"])
    
    prompt = f"""
Sen Türkiye Yüzyılı Maarif Modeli (TYMM) standartlarına hakim, ÖSYM tarzında üst düzey bilişsel ölçme değerlendirme soruları hazırlayan uzman bir Tarih soru yazarısın.

Aşağıdaki parametreler doğrultusunda nitelikli bir 11. Sınıf Tarih sorusu oluştur:

---
### 📋 SORU PARAMETRELERİ
- **Ders:** Tarih (11. Sınıf)
- **Ünite / Tema:** {unite_adi}
- **Öğrenme Çıktısı (Kazanım):** {kazanim_kodu} - {kazanim_tanimi}
- **İlgili Alan Becerileri:** {beceriler}
- **Anahtar Kavramlar:** {kavramlar}
- **Soru Tipi:** {soru_tipi}
- **Zorluk / Bilişsel Düzey:** {zorluk}
{"- **Özel Bağlam / Metin Notu:** " + ek_baglam if ek_baglam else ""}
---

### ✍️ SORU YAZIM KURALLARI VE BİÇİMLENDİRME:
1. **Bağlam Metni (Öncül):**
   - Sorunun başında mutlaka tarihsel bir bağlam (birinci elden arşiv belgesi, seyahatname alıntısı, tarihçi görüşü, karşılaştırma tablosu veya tarihsel olay özeti) yer almalıdır.
   - Metin özgün, tarihsel gerçekliklere sadık ve edebi dili güçlü olmalıdır.
   
2. **Soru Kökü:**
   - Kazanımda hedeflenen beceriyi (analiz, çıkarım, tarihsel empati, karşılaştırma vb.) doğrudan ölçmelidir.
   - "...yargılardan hangisine ulaşılabilir / ulaşılamaz?" veya "...aşağıdakilerden hangisi gösterilebilir / gösterilemez?" şeklinde net olmalıdır.

3. **Seçenekler ve Çözüm (Çoktan Seçmeli ise):**
   - A, B, C, D, E olmak üzere 5 seçenek içermelidir. Çeldiriciler güçlü ve mantıklı olmalıdır.
   - Doğru cevap açıkça belirtilmeli ve detaylı pedogojik "Çözüm Açıklaması" eklenmelidir.

4. **Klasik / Açık Uçlu ise:**
   - Öğrencinin üst düzey düşünme becerisini ortaya koyacak yönlendirici soru maddeleri olmalı.
   - Detaylı ve puanlama kriterlerini içeren bir "Dereceli Puanlama Anahtarı (Rubrik)" eklenmelidir.

Lütfen çıktıyı şık ve okunaklı bir Markdown formatında sun.
"""
    return prompt

# ==========================================
# 3. STREAMLIT ARAYÜZ MİMARİSİ
# ==========================================
st.title("🏛️ TYMM 11. Sınıf Tarih Soru Üreteci")
st.markdown("**Türkiye Yüzyılı Maarif Modeli** ve **ÖSYM** standartlarında bağlam temelli soru ve materyal hazırlama aracı.")

st.divider()

# Sidebar: Parametre Seçimleri
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
    
    soru_tipi = st.radio(
        "Soru Tipi:",
        ["Bağlam Temelli Çoktan Seçmeli (%40 TYMM)", "ÖSYM Tarzı Klasik / Bilişsel (%60)", "Açık Uçlu Senaryo / Analiz Sorusu"]
    )
    
    zorluk = st.select_slider(
        "Zorluk Derecesi:",
        options=["Kolay", "Orta", "Zor (ÖSYM Üst Seviye)", "Derecelendirilmiş / Şampiyon"]
    )

# Ana Ekran
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

# Prompt Üretme ve Gösterim Alanı
st.subheader("🚀 Yapay Zeka Soru Üretim Promptu")

generated_prompt = build_prompt(unite_secimi, kazanim_kodu, kazanim_tanimi, soru_tipi, zorluk, ek_baglam)

st.text_area(
    "Aşağıdaki promptu LLM (Gemini, ChatGPT) modeline yapıştırarak sorunuzu üretebilirsiniz:",
    value=generated_prompt,
    height=320
)

st.success("✅ Prompt başarıyla kurgulandı! Yukarıdaki metni kopyalayıp doğrudan modelinize gönderebilirsiniz.")

