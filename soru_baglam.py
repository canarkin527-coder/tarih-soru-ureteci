import os
import json
import time
from datetime import datetime
import io
import streamlit as st

# Word Dışa Aktarımı için
try:
    import docx
    from docx import Document
    DOCX_MEVCUT = True
except ImportError:
    DOCX_MEVCUT = False

# PDF Okuma için
try:
    import pypdf
    PDF_MEVCUT = True
except ImportError:
    PDF_MEVCUT = False


# ==========================================
# SABİTLER VE YAPILANDIRMA
# ==========================================
MAKS_KAYNAK_KARAKTER_VARSAYILAN = 100000
KAYNAK_KLASORU = "kaynak_kutuphane"
HAVUZ_DOSYASI = "havuz.json"

st.set_page_config(
    page_title="TYMM 11. Sınıf Tarih Soru Üreteci",
    page_icon="📜",
    layout="wide"
)

# Klasör Oluşturma
if not os.path.exists(KAYNAK_KLASORU):
    os.makedirs(KAYNAK_KLASORU)

if "kaynak_metin" not in st.session_state:
    st.session_state.kaynak_metin = ""
if "kaynak_dosya_adlari" not in st.session_state:
    st.session_state.kaynak_dosya_adlari = []
if "uretilen_soru" not in st.session_state:
    st.session_state.uretilen_soru = ""
if "son_uretim_meta" not in st.session_state:
    st.session_state.son_uretim_meta = {}


# ==========================================
# YARDIMCI FONKSİYONLAR (KÜTÜPHANE VE HAVUZ)
# ==========================================
def yuklenen_dosyalari_isle(yuklenen_dosyalar):
    """Yüklenen PDF/TXT dosyalarını diske kaydeder."""
    for dosya in yuklenen_dosyalar:
        dosya_yolu = os.path.join(KAYNAK_KLASORU, dosya.name)
        with open(dosya_yolu, "wb") as f:
            f.write(dosya.getbuffer())

def kutuphaneyi_diskten_yukle():
    """Disk klasöründeki tüm PDF ve TXT'leri okuyup tek metinde birleştirir."""
    birlesik_metin = ""
    dosya_adlari = []
    
    if not os.path.exists(KAYNAK_KLASORU):
        return birlesik_metin, dosya_adlari

    for dosya_adi in sorted(os.listdir(KAYNAK_KLASORU)):
        dosya_yolu = os.path.join(KAYNAK_KLASORU, dosya_adi)
        if dosya_adi.endswith(".txt"):
            dosya_adlari.append(dosya_adi)
            with open(dosya_yolu, "r", encoding="utf-8", errors="ignore") as f:
                birlesik_metin += f"\n--- DOSYA: {dosya_adi} ---\n" + f.read()
        elif dosya_adi.endswith(".pdf") and PDF_MEVCUT:
            dosya_adlari.append(dosya_adi)
            try:
                reader = pypdf.PdfReader(dosya_yolu)
                pdf_metin = ""
                for sayfa in reader.pages:
                    pdf_metin += sayfa.extract_text() or ""
                birlesik_metin += f"\n--- DOSYA: {dosya_adi} ---\n" + pdf_metin
            except Exception as e:
                st.error(f"PDF okunurken hata: {dosya_adi} - {e}")

    return birlesik_metin, dosya_adlari

def havuzu_yukle():
    """JSON dosyasından havuz verilerini getirir."""
    if os.path.exists(HAVUZ_DOSYASI):
        try:
            with open(HAVUZ_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def havuza_kaydet(yeni_kayit):
    """Yeni üretilen soru setini JSON havuzuna ekler."""
    mevcut = havuzu_yukle()
    mevcut.insert(0, yeni_kayit)
    with open(HAVUZ_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(mevcut, f, ensure_ascii=False, indent=2)

def havuzdan_sil(kayit_id):
    """ID'ye göre kaydı havuzdan siler."""
    mevcut = havuzu_yukle()
    guncel = [k for k in mevcut if k.get("id") != kayit_id]
    with open(HAVUZ_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(guncel, f, ensure_ascii=False, indent=2)


# ==========================================
# WORD (DOCX) DIŞA AKTARMA FONKSİYONLARI
# ==========================================
def ham_metin_word(markdown_metin, ust_bilgi=""):
    """Tek bir Markdown soru çıktısını Word belgesine dönüştürür."""
    doc = Document()
    if ust_bilgi:
        doc.add_heading(ust_bilgi, level=2)
        doc.add_paragraph(f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        doc.add_paragraph("-" * 40)
    
    for satir in markdown_metin.split("\n"):
        satir_str = satir.strip()
        if satir_str.startswith("# "):
            doc.add_heading(satir_str.replace("# ", ""), level=1)
        elif satir_str.startswith("## "):
            doc.add_heading(satir_str.replace("## ", ""), level=2)
        elif satir_str.startswith("### "):
            doc.add_heading(satir_str.replace("### ", ""), level=3)
        else:
            doc.add_paragraph(satir)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def tek_kayit_word(kayit):
    ust_bilgi = f"Ünite: {kayit.get('unite')} | Kod: {kayit.get('cikti_kod')} | Zorluk: {kayit.get('zorluk')}"
    return ham_metin_word(kayit.get("icerik", ""), ust_bilgi=ust_bilgi)

def coklu_kayit_word(kayitlar):
    """Havuzdaki tüm kayıtları tek bir Word belgesinde birleştirir."""
    doc = Document()
    doc.add_heading("Türkiye Yüzyılı Maarif Modeli - 11. Sınıf Tarih Soru Havuzu", level=1)
    
    for idx, kayit in enumerate(kayitlar, 1):
        doc.add_heading(f"{idx}. {kayit.get('cikti_kod')} - {kayit.get('soru_kategorisi')}", level=2)
        doc.add_paragraph(f"Ünite: {kayit.get('unite')} | Zorluk: {kayit.get('zorluk')} | Tarih: {kayit.get('zaman')}")
        doc.add_paragraph(kayit.get("icerik", ""))
        doc.add_page_break()
        
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ==========================================
# MOCK LLM ÜRETİM FONKSİYONU
# ==========================================
def uret_otomatik_parcali(saglayici, api_key, model, temel_parametreler, toplam_soru, ilerleme):
    """
    LLM API çağrısını gerçekleştiren fonksiyon.
    Gerçek API entegrasyonu (OpenAI / Google Gemini) bu blok içerisine yazılır.
    """
    ilerleme("Kaynak metin analiz ediliyor...")
    time.sleep(0.8)
    ilerleme(f"Bağlam temelli {toplam_soru} adet soru üretiliyor...")
    time.sleep(1.2)
    
    # Örnek çıktı simülasyonu
    ornek_cikti = f"""# {temel_parametreler['unite']} — {temel_parametreler['cikti_kod']} Soru Seti

**Kategori:** {temel_parametreler['soru_kategorisi']} | **Zorluk:** {temel_parametreler['zorluk']}

---

### Soru 1
19. yüzyıl Osmanlı Devleti'nde meydana gelen idari ve hukuki düzenlemeler dikkate alındığında...

**A)** Yalnız I  
**B)** Yalnız II  
**C)** I ve II  
**D)** II ve III  
**E)** I, II ve III  

**Cevap:** C  
**Çözüm / Bağlam Analizi:** Metindeki maddeler incelendiğinde merkezi otoritenin güçlendirilmesi hedeflenmiştir.
"""
    return ornek_cikti


# ==========================================
# YAN PANEL (SIDEBAR) — PARAMETRELER
# ==========================================
with st.sidebar:
    st.title("⚙️ Üretim Parametreleri")
    
    saglayici = st.selectbox("LLM Sağlayıcı:", ["Google Gemini", "OpenAI"])
    model_secimi = st.selectbox("Model:", ["gemini-1.5-pro", "gpt-4o"] if saglayici == "OpenAI" else ["gemini-1.5-pro", "gemini-1.5-flash"])
    api_key = st.text_input("API Anahtarı:", type="password")
    
    st.divider()
    
    unite_secimi = st.selectbox("Ünite Seçimi:", [
        "1. Ünite: 19. ve 20. Yüzyıl Başlarında Osmanlı Devleti",
        "2. Ünite: 20. Yüzyıl Başlarında Dünya ve Osmanlı"
    ])
    
    cikti_kod = st.text_input("Çıktı Kodu:", value="TAR.11.1.1")
    cikti_tam = st.text_area("Öğrenme Çıktısı Tanımı:", value="19. yüzyılda Osmanlı Devleti'nin idari ve sosyal yapısındaki değişimleri analiz eder.")
    
    surec_secimi = st.multiselect(
        "Süreç Bileşenleri:",
        ["Değişimi Mütalaa Etme", "Tarihsel Kanıt Kullanma", "Neden-Sonuç İlişkisi Kurma"],
        default=["Tarihsel Kanıt Kullanma"]
    )
    
    soru_kategorisi = st.selectbox("Soru Kategorisi:", ["Bağlam Temelli Çoktan Seçmeli", "Açık Uçlu / Analiz"])
    zorluk = st.select_slider("Zorluk Seviyesi:", options=["Kolay", "Orta", "Zor", "ÖSYM Ayarı"], value="ÖSYM Ayarı")
    soru_sayisi = st.number_input("Soru Sayısı:", min_value=1, max_value=20, value=5)
    ek_baglam = st.text_area("Ek Talimatlar / Özel Notlar:", placeholder="Örn: Sadece 19. yüzyıl ıslahatlarına odaklanılsın.")


# İlk çalıştırmada diskteki kütüphaneyi yükle
if not st.session_state.kaynak_metin and os.path.exists(KAYNAK_KLASORU):
    metin, adlar = kutuphaneyi_diskten_yukle()
    st.session_state.kaynak_metin = metin
    st.session_state.kaynak_dosya_adlari = adlar


# ==========================================
# ANA EKRAN — KAYNAK KÜTÜPHANESİ
# ==========================================
st.title("📜 Türkiye Yüzyılı Maarif Modeli - Soru Üretim Paneli")

st.subheader("📚 Kaynak Kütüphanesi")
st.caption(
    "Diskteki `kaynak_kutuphane/` klasöründen yüklenen ders kitabı, makale veya arşiv belgeleri. "
    "Sorular öncelikle buradaki metinlere dayandırılır."
)

with st.expander("📁 Kaynak Dosyaları Yönet & Önizle", expanded=False):
    kutuphane_dosyalari = st.file_uploader(
        "Kütüphaneye yeni PDF/TXT belgeleri ekleyin:",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="Yüklenen dosyalar yerel klasöre kaydedilir ve sonraki oturumlarda da kullanılır."
    )
    
    if kutuphane_dosyalari:
        with st.spinner("Dosyalar kütüphaneye kaydediliyor..."):
            yuklenen_dosyalari_isle(kutuphane_dosyalari)
            metin, adlar = kutuphaneyi_diskten_yukle()
            st.session_state.kaynak_metin = metin
            st.session_state.kaynak_dosya_adlari = adlar
            st.success(f"{len(kutuphane_dosyalari)} yeni dosya kütüphaneye eklendi!")
            st.rerun()

    if st.session_state.get("kaynak_dosya_adlari"):
        st.markdown("**Aktif Kütüphane İçeriği:**")
        for ad in st.session_state.kaynak_dosya_adlari:
            st.markdown(f" - 📄 `{ad}`")
            
        maks_karakter = st.number_input(
            "Model Gönderim Karakter Limiti:",
            min_value=10000,
            max_value=500000,
            value=MAKS_KAYNAK_KARAKTER_VARSAYILAN,
            step=10000,
            help="Çok büyük belgelerde token kotasını aşmamak için metni kırpar."
        )
        
        aktif_metin = st.session_state.kaynak_metin[:maks_karakter]
        if len(st.session_state.kaynak_metin) > maks_karakter:
            st.info(f"⚠️ Kaynak metni toplam {len(st.session_state.kaynak_metin)} karakter. İlk {maks_karakter} karakter modele aktarılacak.")
            
        with st.popover("📖 Birleştirilmiş Metin Önizlemesi"):
            st.text_area("Yüklü Metin İçeriği", value=aktif_metin, height=300, disabled=True)
    else:
        st.info("Kütüphanede henüz dosya yok. Dilerseniz yukarıdan PDF veya TXT belgeleri yükleyebilirsiniz.")
        aktif_metin = ""

st.divider()

# ==========================================
# ÜRETİM BUTONU VE YÖNETİMİ
# ==========================================
uretim_baslat = st.button("🚀 Soru Setini Üret", type="primary", use_container_width=True)

if uretim_baslat:
    if not surec_secimi:
        st.error("Lütfen en az bir süreç bileşeni (alt başlık) seçin.")
    elif not api_key:
        st.error(f"Lütfen geçerli bir {saglayici} API anahtarı girin.")
    else:
        durum_kutusu = st.empty()
        ilerleme_bar = st.progress(0)
        
        def ilerleme_guncelle(mesaj):
            durum_kutusu.info(f"⏳ {mesaj}")

        try:
            ilerleme_guncelle("Prompt hazırlanıyor ve istek oluşturuluyor...")
            
            temel_p = {
                "unite": unite_secimi,
                "cikti_kod": cikti_kod,
                "cikti_tam": cikti_tam,
                "surec_metinleri": surec_secimi,
                "soru_kategorisi": soru_kategorisi,
                "zorluk": zorluk,
                "kaynak_metin": aktif_metin,
                "ek_baglam": ek_baglam
            }
            
            ilerleme_bar.progress(30)
            
            ham_yanit = uret_otomatik_parcali(
                saglayici=saglayici,
                api_key=api_key,
                model=model_secimi,
                temel_parametreler=temel_p,
                toplam_soru=soru_sayisi,
                ilerleme=ilerleme_guncelle
            )
            
            ilerleme_bar.progress(100)
            durum_kutusu.empty()
            ilerleme_bar.empty()
            
            # Üretim sonuçlarını oturum durumuna kaydet
            st.session_state.uretilen_soru = ham_yanit
            st.session_state.son_uretim_meta = {
                "unite": unite_secimi,
                "cikti_kod": cikti_kod,
                "cikti_tam": cikti_tam,
                "surecler": surec_secimi,
                "soru_kategorisi": soru_kategorisi,
                "zorluk": zorluk,
                "soru_sayisi": soru_sayisi,
                "model": f"{saglayici} ({model_secimi})",
                "zaman": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.success("✨ Sorular başarıyla üretildi!")
            
        except Exception as e:
            durum_kutusu.empty()
            ilerleme_bar.empty()
            st.error(f"Üretim sırasında bir hata oluştu: {e}")

# ==========================================
# ANA EKRAN — SEKMELER (ÇIKTI VE HAVUZ)
# ==========================================
tab_uretim, tab_havuz = st.tabs(["📝 Üretilen Sorular", "🗄️ Soru Havuzu ve Dışa Aktarma"])

# ------------------------------------------
# SEKME 1: ÜRETİLEN SORULAR
# ------------------------------------------
with tab_uretim:
    if st.session_state.uretilen_soru:
        meta = st.session_state.son_uretim_meta
        
        st.markdown("### 📋 Üretim Detayları")
        st.caption(
            f"**Kategori:** {meta.get('soru_kategorisi')} | **Zorluk:** {meta.get('zorluk')} | "
            f"**Soru Sayısı:** {meta.get('soru_sayisi')} | **Model:** {meta.get('model')} | **Tarih:** {meta.get('zaman')}"
        )
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if DOCX_MEVCUT:
                word_tampon = ham_metin_word(
                    markdown_metin=st.session_state.uretilen_soru,
                    ust_bilgi=f"Ünite: {meta.get('unite')} | Çıktı: {meta.get('cikti_kod')} | Zorluk: {meta.get('zorluk')}"
                )
                st.download_button(
                    label="📄 Word (.docx) Olarak İndir",
                    data=word_tampon,
                    file_name=f"TYMM_Tarih_11_{meta.get('cikti_kod')}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            else:
                st.warning("Word indirme için `python-docx` kütüphanesi gerekli.")

        with c2:
            if st.button("📥 Soru Havuzuna Kaydet", use_container_width=True):
                kayit_id = f"{meta.get('cikti_kod')}_{int(time.time())}"
                yeni_kayit = {
                    "id": kayit_id,
                    "unite": meta.get("unite"),
                    "cikti_kod": meta.get("cikti_kod"),
                    "cikti_tam": meta.get("cikti_tam"),
                    "surecler": meta.get("surecler"),
                    "soru_kategorisi": meta.get("soru_kategorisi"),
                    "zorluk": meta.get("zorluk"),
                    "soru_sayisi": meta.get("soru_sayisi"),
                    "model": meta.get("model"),
                    "zaman": meta.get("zaman"),
                    "icerik": st.session_state.uretilen_soru
                }
                havuza_kaydet(yeni_kayit)
                st.success("Soru seti başarıyla kalıcı havuza kaydedildi!")

        st.divider()
        st.markdown(st.session_state.uretilen_soru)
    else:
        st.info("Henüz soru üretilmedi. Sol panelden parametreleri seçip **Soru Setini Üret** butonuna basın.")

# ------------------------------------------
# SEKME 2: SORU HAVUZU VE DIŞA AKTARMA
# ------------------------------------------
with tab_havuz:
    havuz_verisi = havuzu_yukle()
    
    if not havuz_verisi:
        st.info("Soru havuzu şu anda boş. Ürettiğiniz soru setlerini **Soru Havuzuna Kaydet** butonunu kullanarak buraya aktarabilirsiniz.")
    else:
        st.markdown(f"### 🗄️ Havuzdaki Soru Setleri ({len(havuz_verisi)} Kayıt)")
        
        if DOCX_MEVCUT:
            toplu_word = coklu_kayit_word(havuz_verisi)
            st.download_button(
                label="📦 Tüm Havuzu Tek Word Belgesi Olarak İndir (.docx)",
                data=toplu_word,
                file_name=f"TYMM_11_Tarih_Soru_Havuzu_Tumu_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
        st.divider()
        
        for idx, kayit in enumerate(havuz_verisi):
            baslik = (
                f"[{kayit.get('cikti_kod')}] {kayit.get('soru_kategorisi')} — "
                f"{kayit.get('zorluk')} ({kayit.get('soru_sayisi')} Soru) — {kayit.get('zaman')}"
            )
            
            with st.expander(baslik, expanded=False):
                st.markdown(f"**Ünite:** {kayit.get('unite')}")
                st.markdown(f"**Öğrenme Çıktısı:** {kayit.get('cikti_tam')}")
                if kayit.get("surecler"):
                    st.markdown("**Süreç Bileşenleri:** " + ", ".join(kayit["surecler"]))
                st.caption(f"Model: {kayit.get('model')} | Kayıt ID: `{kayit.get('id')}`")
                
                col_h1, col_h2 = st.columns([1, 1])
                
                with col_h1:
                    if DOCX_MEVCUT:
                        tekli_word = tek_kayit_word(kayit)
                        st.download_button(
                            label="📄 Bu Kaydı Word Olarak İndir",
                            data=tekli_word,
                            file_name=f"Soru_{kayit.get('cikti_kod')}_{kayit.get('id')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_{kayit.get('id')}",
                            use_container_width=True
                        )
                
                with col_h2:
                    if st.button("🗑️ Kaydı Havuzdan Sil", key=f"del_{kayit.get('id')}", use_container_width=True):
                        havuzdan_sil(kayit.get("id"))
                        st.warning("Kayıt silindi.")
                        st.rerun()

                st.divider()
                st.markdown(kayit.get("icerik", ""))
