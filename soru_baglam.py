import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_MEVCUT = True
except ImportError:
    ANTHROPIC_MEVCUT = False

try:
    import google.generativeai as genai
    GEMINI_MEVCUT = True
except ImportError:
    GEMINI_MEVCUT = False

try:
    from pypdf import PdfReader
    PYPDF_MEVCUT = True
except ImportError:
    PYPDF_MEVCUT = False

MAKS_KAYNAK_KARAKTER_VARSAYILAN = 150000  # ~35-40 bin token; Claude/Gemini'nin geniş bağlam penceresine göre makul bir varsayılan
KUTUPHANE_KLASORU = Path(__file__).parent / "kaynak_kutuphane"  # Yüklenen dosyaların kalıcı olarak saklandığı yerel klasör
KUTUPHANE_KLASORU.mkdir(exist_ok=True)

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
    """Oturum durumunu (geçmiş, favoriler, üretilen soru, kaynak metin) başlatır.
    Kaynak kütüphanesi diskteki kalıcı klasörden otomatik olarak yüklenir."""
    if "gecmis" not in st.session_state:
        st.session_state.gecmis = []
    if "favoriler" not in st.session_state:
        st.session_state.favoriler = []
    if "uretilen_soru" not in st.session_state:
        st.session_state.uretilen_soru = None
    if "kutuphane_yuklendi" not in st.session_state:
        # Uygulama ilk açıldığında diskteki mevcut kütüphaneyi oku
        metin, adlar = kutuphaneyi_diskten_yukle()
        st.session_state.kaynak_metin = metin
        st.session_state.kaynak_dosya_adlari = adlar
        st.session_state.kutuphane_yuklendi = True


def pdf_metin_cikar(dosya_yolu):
    """Diskteki bir PDF dosyasından metin çıkarır."""
    reader = PdfReader(dosya_yolu)
    parcalar = []
    for sayfa in reader.pages:
        try:
            parcalar.append(sayfa.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parcalar).strip()


def txt_metin_cikar(dosya_yolu):
    """Diskteki bir .txt dosyasından metin çıkarır (birden çok kodlamayı dener)."""
    ham = Path(dosya_yolu).read_bytes()
    for kodlama in ("utf-8", "windows-1254", "iso-8859-9", "latin-1"):
        try:
            return ham.decode(kodlama).strip()
        except (UnicodeDecodeError, AttributeError):
            continue
    return ham.decode("utf-8", errors="ignore").strip()


@st.cache_data(show_spinner=False)
def dosyadan_metin_cikar(dosya_yolu_str, degisiklik_zamani):
    """Diskteki bir dosyadan metin çıkarır. `degisiklik_zamani` önbelleği geçersiz kılmak için kullanılır
    (dosya değişirse Streamlit önbelleği otomatik yeniler)."""
    dosya_yolu = Path(dosya_yolu_str)
    if dosya_yolu.suffix.lower() == ".pdf":
        if not PYPDF_MEVCUT:
            return ""
        return pdf_metin_cikar(dosya_yolu)
    return txt_metin_cikar(dosya_yolu)


def dosyayi_kutuphaneye_kaydet(yuklenen_dosya):
    """Streamlit'ten gelen yüklenen dosyayı kalıcı kütüphane klasörüne yazar, çakışan adları numaralandırır."""
    hedef = KUTUPHANE_KLASORU / yuklenen_dosya.name
    sayac = 1
    while hedef.exists():
        hedef = KUTUPHANE_KLASORU / f"{Path(yuklenen_dosya.name).stem}_{sayac}{Path(yuklenen_dosya.name).suffix}"
        sayac += 1
    hedef.write_bytes(yuklenen_dosya.getbuffer())
    return hedef


def kutuphaneyi_diskten_yukle():
    """Kütüphane klasöründeki tüm dosyaları okuyup birleşik kaynak metnini ve dosya adlarını döndürür."""
    tum_metin = []
    dosya_adlari = []
    for dosya_yolu in sorted(KUTUPHANE_KLASORU.glob("*")):
        if dosya_yolu.suffix.lower() not in (".pdf", ".txt"):
            continue
        try:
            metin = dosyadan_metin_cikar(str(dosya_yolu), dosya_yolu.stat().st_mtime)
        except Exception as e:
            st.error(f"'{dosya_yolu.name}' okunurken hata oluştu: {e}")
            continue
        if metin:
            tum_metin.append(f"### Kaynak: {dosya_yolu.name}\n{metin}")
            dosya_adlari.append(dosya_yolu.name)
        else:
            st.warning(f"'{dosya_yolu.name}' içinden metin çıkarılamadı (taranmış görsel PDF olabilir).")
    return "\n\n---\n\n".join(tum_metin), dosya_adlari


def yuklenen_dosyalari_isle(dosyalar):
    """Yeni yüklenen dosyaları diske kalıcı olarak kaydeder."""
    for dosya in dosyalar:
        try:
            dosyayi_kutuphaneye_kaydet(dosya)
        except Exception as e:
            st.error(f"'{dosya.name}' diske kaydedilirken hata oluştu: {e}")


def soru_uret_api(api_key, model, prompt):
    """Anthropic API'sini çağırarak promptu doğrudan bir soruya dönüştürür.
    Yanıt token sınırına takılıp yarım kaldıysa bunu tespit edip kullanıcıyı uyarır."""
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )
    parcalar = [blok.text for blok in response.content if blok.type == "text"]
    metin = "\n".join(parcalar)
    if response.stop_reason == "max_tokens":
        metin += (
            "\n\n---\n⚠️ **UYARI:** Yanıt, model çıktı sınırına (token limiti) takıldığı için yarım kalmış olabilir. "
            "Soru sayısını azaltıp tekrar denemenizi veya soruları iki ayrı istek hâlinde ürettirmenizi öneririz."
        )
    return metin


def soru_uret_gemini(api_key, model, prompt):
    """Google Gemini API'sini çağırarak promptu doğrudan bir soruya dönüştürür.
    Yanıt token sınırına takılıp yarım kaldıysa bunu tespit edip kullanıcıyı uyarır."""
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(max_output_tokens=16000)
    )
    metin = response.text
    try:
        if response.candidates[0].finish_reason == 2:  # MAX_TOKENS
            metin += (
                "\n\n---\n⚠️ **UYARI:** Yanıt, model çıktı sınırına (token limiti) takıldığı için yarım kalmış olabilir. "
                "Soru sayısını azaltıp tekrar denemenizi veya soruları iki ayrı istek hâlinde ürettirmenizi öneririz."
            )
    except (IndexError, AttributeError):
        pass
    return metin


def build_prompt(unite_adi, kazanim_kodu, kazanim_tanimi, soru_tipi, zorluk,
                  odak_kavramlar, ek_baglam, soru_sayisi, kaynak_metin=""):
    """Seçilen parametrelere göre LLM'e gönderilecek promptu oluşturur."""
    tum_kavramlar = MUFREDAT_11_SINIF[unite_adi]["kavramlar"]
    beceriler = ", ".join(MUFREDAT_11_SINIF[unite_adi]["beceriler"])

    # Kullanıcı belirli kavramlar seçtiyse onları, seçmediyse tüm kavramları kullan
    kavramlar = ", ".join(odak_kavramlar) if odak_kavramlar else ", ".join(tum_kavramlar)

    uslup_blok = """
0. **Yazım Üslubu (ZORUNLU):**
   - Metinler bir yapay zekâ tarafından değil, alanında deneyimli bir tarih öğretmeni/soru yazarı tarafından kaleme alınmış gibi doğal, akıcı ve özgün bir Türkçeyle yazılmalıdır.
   - Yapay zekâ metinlerine özgü basmakalıp açılışlardan ("Günümüzde...", "Tarih boyunca...", "Bilindiği gibi...", "Şüphesiz ki..." gibi klişe girişlerden), aşırı sıfat yığmaktan ve yapay/şablon cümle kalıplarından kaçınılmalıdır.
   - Her bağlam metni kendine özgü, önceki metinlerin kalıbını tekrar etmeyen bir anlatım ve kurguyla yazılmalıdır; seri üretim hissi vermemelidir.
"""

    dogruluk_blok = """
0b. **Tarihsel Doğruluk ve Halüsinasyon Önleme (ZORUNLU):**
   - Kaynak materyal (aşağıda "YÜKLENEN KAYNAK MATERYAL(LER)" varsa) yüklenmişse, bağlam metinlerindeki TÜM somut bilgi (tarih, kişi, olay, sayısal veri) o kaynağa dayanmalıdır; kaynakta yer almayan uydurma bir tarih/isim/olay eklenmemelidir.
   - Kaynak materyal yüklenmemişse iki yol izlenebilir: (a) genel olarak bilinen, tarihçilerce doğrulanmış gerçek olay/kişi/tarihleri kullan, ya da (b) tamamen kurgusal bir öncül kullanacaksan bunu gerçek bir tarihî kişiye ait olduğu izlenimi verecek şekilde SUNMA (ör. gerçek bir tarihî kişiye ait olmayan bir sözü ona atfetme, var olmayan bir arşiv belgesine gerçek bir kod/tarih numarası uydurma). Kurgusal bir karakter kullanıyorsan bunu jenerik bir isimle (ör. "dönemin bir sefaret kâtibi", "bölgeden geçen bir seyyah") yap; gerçek, doğrulanabilir bir tarihî şahsiyet gibi sunma.
   - Emin olmadığın spesifik bir rakam, tarih ya da alıntı varsa, onu icat etmek yerine daha genel ama doğru bir ifadeyle (ör. "yüzyılın ortalarında", "kayda değer bir artışla") yaz.
   - Sorunun doğru cevabı ve çözüm açıklaması, gerçek tarihsel bilgiyle çelişmemelidir; kurgusal bağlam kullanılsa bile çıkarımlar tarihsel mantığa ve bilinen genel çerçeveye sadık kalmalıdır.
"""

    coktan_secmeli_blok = """
3. **Seçenekler ve Çözüm (Çoktan Seçmeli ise):**
   - A, B, C, D, E olmak üzere 5 seçenek içermelidir.
   - **Seçenek Uzunluğu (ZORUNLU):** Tüm seçenekler kelime sayısı, satır uzunluğu, dil yapısı ve karmaşıklık bakımından birbirine YAKIN ve DENGELİ olmalıdır. Doğru seçenek diğerlerinden daha uzun, daha detaylı veya daha açıklayıcı yazılarak öğrenciye görsel bir ipucu verilmemelidir.
   - "Hepsi", "Hiçbiri", "A ve B" gibi öğrencinin muhakeme yapmadan eleyebileceği/seçebileceği kapsayıcı seçenekler KESİNLİKLE kullanılmamalıdır. Her seçenek bağımsız bir yargı veya bilgi içermelidir.
   - Seçeneklerde bağlam metnindeki bir cümle veya kelime öbeği birebir/aynen tekrar edilmemeli; metindeki fikir farklı kelimelerle (anlamca özdeş ama biçimce farklı) ifade edilmelidir. Aksi hâlde öğrenci anlamadan görsel eşleştirmeyle doğru cevabı bulabilir.
   - Çeldiriciler rastgele veya "sadece seçenek sayısını tamamlamak için yazılmış bariz yanlış" ifadeler OLMAMALI; konuyu eksik öğrenen veya yanlış yapılandıran bir öğrencinin gerçekten düşebileceği kavram yanılgılarından veya hatalı akıl yürütmelerden seçilmelidir.
   - Doğru cevap açıkça belirtilmeli ve her seçenek için (doğru dâhil) kısa gerekçelerin yer aldığı detaylı pedagojik bir "Çözüm Açıklaması" eklenmelidir.
"""

    acik_uclu_blok = """
4. **Klasik / Açık Uçlu ise:**
   - Öğrencinin üst düzey düşünme becerisini ortaya koyacak yönlendirici soru maddeleri olmalı.
   - Detaylı ve puanlama kriterlerini içeren bir "Dereceli Puanlama Anahtarı (Rubrik)" eklenmelidir.
"""

    baglam_temelli_mi = "Bağlam Temelli" in soru_tipi
    baglam_soru_sayisi = max(soru_sayisi, 5) if baglam_temelli_mi else soru_sayisi

    baglam_temelli_blok = f"""
5. **Bağlam Temelli Soru Kurgusu (TYMM Bağlam Temelli Soru Yazım Kılavuzu — ZORUNLU SÜREÇ):**

   Aşağıdaki 5 adımlı süreci sırasıyla, atlamadan uygula:

   **ADIM 1 — Hedefin Netleştirilmesi:** Ölçülecek öğrenme çıktısı ve bu çıktıya ait süreç bileşenlerini (alt becerileri) net biçimde ayrıştır. Her soru, bu süreç bileşenlerinden birini hedeflemelidir.

   **ADIM 2 — Bağlamın Kurgulanması:**
   - Bağlam metni tam olarak İKİ (2) PARAGRAFTAN oluşmalıdır — ne tek paragraf ne de üçten fazla. İlk paragraf durumu/olayı/belgeyi tanıtmalı, ikinci paragraf ayrıntı, gelişme veya farklı bir bakış açısı/veri sunarak metni derinleştirmelidir.
   - Tarih dersi için özgün, günlük-hayat karşılığı: bir tarihçinin/araştırmacının karşılaşacağı türden "birincil veya ikincil kaynak" niteliğinde bir materyal (bir hatırat kesiti, dönemin gazete haberi, arşiv belgesi, seyahatname parçası, müze objesi tasviri, tarihçi değerlendirmesi, edebî metin/mektup vb.) kullanılmalıdır. Bağlam yalnızca bir "dekor" olmamalı, öğrenciye gerçek bir tarihçinin yapacağı türden karmaşık ve yapılandırılmamış bir çıkarım görevi sunmalıdır.
   - Belirli bir sosyoekonomik çevreye özgü, dar ve yabancılaştırıcı referanslardan kaçınılmalı; öğrencinin kolayca kendini içine yerleştirebileceği, erişilebilir ve özgün (authentic) bir kurgu tercih edilmelidir.
   - Metindeki dil yapısı, söz varlığı ve cümle uzunluğu 11. sınıf öğrencisinin bilişsel düzeyine uygun olmalı; gereksiz süslü/karmaşık cümlelerden, dekoratif ayrıntılardan kaçınılarak bilişsel yük en aza indirilmelidir.

   **ADIM 3 — Süreç Bileşenlerini Ölçen Soruların Hazırlanması:**
   - Bu TEK bağlam metnine dayanan TAM OLARAK {baglam_soru_sayisi} farklı soru üretilmelidir; bu sayının altında kalınmamalı, gerekirse bu kadar soruyu kaldıracak zenginlikte kurgulanmalıdır.
   - Sorular öğrenme çıktısının farklı süreç bileşenlerini/bilişsel boyutlarını ölçmelidir (ör. doğrudan bilgi/çıkarım, neden-sonuç ilişkisi, karşılaştırma, yargıya ulaşma/ulaşamama, genelleme). Birbirinin aynısı veya yakın varyasyonu olan sorular üretilmemelidir.
   - **İpucu Zinciri Yasağı (ZORUNLU):** Sorular arasında bağımlılık kurulmamalıdır. Bir sorunun cevabı diğer sorunun ön koşulu olmamalı; "Bir önceki soruda bulduğunuz sonuca göre..." tarzı ifadeler KESİNLİKLE kullanılmamalıdır. Bunun yerine her soru "Bu parçaya göre...", "Metinde anlatılanlara göre..." gibi ortak bağlama bağımsız şekilde atıfta bulunmalı; ilk soruyu cevaplayamayan bir öğrenci de metne dönüp ikinci soruyu rahatça cevaplayabilmelidir.
   - Soru kökü kuralları: (a) Çift olumsuzluk içeren ifadeler ("...olmadığı söylenemez?" gibi) kullanılmamalı; olumsuzluk gerekiyorsa tek ve net olmalı, kelime koyu/altı çizili vurgulanmalıdır. (b) "Sizce", "Size göre" gibi öznel ifadeler kullanılmamalı; "Metne göre", "Bu parçadan hareketle" gibi metne dayalı nesnel ifadeler tercih edilmelidir. (c) Soru kökünde konu tekrar anlatılmamalı/genişletilmemeli; bilgi bağlamda kalmalı, soru kökü yalnızca öğrenciyi cevaba yönlendirmelidir.
   - Bağlam metni yalnızca bir kez, sorular grubunun en başında verilmeli; her soru öncesinde tekrarlanmamalı, sorular metnin altında "1.", "2.", "3." ... şeklinde sıralanmalıdır.

   **ADIM 4 — Güçlü Çeldiricilerin Yapılandırılması:** Her sorunun 5 seçeneğindeki (A-E) yanlış seçenekler; metinle ilişkili ama ustaca yanıltıcı olmalıdır — kısmen doğru ama eksik bilgi, metinde geçen ama soruyla ilgisiz bir ayrıntı, tarihsel olarak doğru ama bu bağlamda geçersiz bir bilgi ya da mantık hatası içeren makul görünümlü ifadeler gibi teknikler kullanılmalıdır. Bkz. madde 3'teki seçenek uzunluğu ve biçim kuralları (eşit uzunluk, "Hepsi/Hiçbiri" yasağı, metinden birebir alıntı yasağı) bağlam temelli sorularda da aynı sıkılıkla geçerlidir.

   **ADIM 5 — Bağlamın İşlevselliğinin Test Edilmesi (ZORUNLU ÖZ-DENETİM):** Her soruyu yazdıktan sonra şu soruyu kendine sor: "Öğrenci bu metni hiç okumadan, sadece ön bilgisiyle veya seçenekleri eleyerek bu soruyu cevaplayabilir mi?" Cevap "evet" ise o soru İŞLEVSİZ demektir; bağlamı ve/veya soruyu, cevabın mutlaka metindeki bilgiye/çıkarıma dayanacağı şekilde yeniden kurgula. Nihai çıktıya bu öz-denetimden geçtiğini gösteren bir "Bağlam İşlevsellik Notu" eklemene gerek yok; sadece bu testi geçen sorular üret.
"""

    kaynak_blok = ""
    if kaynak_metin:
        kaynak_blok = f"""
7. **Yüklenen Kaynak Materyal Kullanımı (ZORUNLU ÖNCELİK):**
   - Aşağıda öğretmenin yüklediği kitap/döküman parçaları yer almaktadır. Bağlam metinlerini ve soruları KURGUSAL olarak değil, ÖNCELİKLE bu kaynaklardaki bilgi, olay, kişi, tarih ve alıntılara dayanarak oluştur.
   - Kaynaklarda birden fazla dosya varsa, kazanıma ve üniteye en uygun olan bölüm(ler)i seç; konuyla ilgisiz kısımları kullanma.
   - Kaynaktan doğrudan uzun alıntı kopyalamak yerine, kaynaktaki bilgiyi kendi tarihsel bağlam metnini yazarken zemin olarak kullan; gerekirse kısa (en fazla 1-2 cümlelik) doğrudan alıntılara yer verebilirsin.
   - Kaynakta kazanımla ilgili yeterli bilgi yoksa, bunu belirt ve genel tarihî bilgini kullanarak devam et.

---
### 📚 YÜKLENEN KAYNAK MATERYAL(LER)
{kaynak_metin}
---
"""

    prompt = f"""Sen Türkiye Yüzyılı Maarif Modeli (TYMM) Bağlam Temelli Çoktan Seçmeli Soru Yazım Kılavuzu'na ve ÖSYM ölçme-değerlendirme standartlarına hakim, üst düzey bilişsel soru hazırlayan, alanında yılların verdiği tecrübeye sahip bir Tarih öğretmeni/soru yazarısın.

Aşağıdaki parametreler doğrultusunda TAM OLARAK {baglam_soru_sayisi if baglam_temelli_mi else soru_sayisi} adet nitelikli 11. Sınıf Tarih sorusu oluştur. Bu sayı bir üst sınır değil, kesin bir hedeftir; daha az soru üretip bırakmak KABUL EDİLEMEZ.

---
### 📋 SORU PARAMETRELERİ
- **Ders:** Tarih (11. Sınıf)
- **Ünite / Tema:** {unite_adi}
- **Öğrenme Çıktısı (Kazanım):** {kazanim_kodu} - {kazanim_tanimi}
- **İlgili Alan Becerileri:** {beceriler}
- **Anahtar Kavramlar:** {kavramlar}
- **Soru Tipi:** {soru_tipi}
- **Zorluk / Bilişsel Düzey:** {zorluk}
- **Üretilecek Soru Sayısı (KESİN):** {baglam_soru_sayisi if baglam_temelli_mi else soru_sayisi}
{"- **Özel Bağlam / Metin Notu:** " + ek_baglam if ek_baglam else ""}
---
{kaynak_blok}
### ✍️ SORU YAZIM KURALLARI VE BİÇİMLENDİRME:
{uslup_blok}
{dogruluk_blok}
1. **Bağlam Metni (Öncül):**
   - Sorunun başında mutlaka tarihsel bir bağlam (birinci elden arşiv belgesi, seyahatname alıntısı, tarihçi görüşü, karşılaştırma tablosu veya tarihsel olay özeti) yer almalıdır.
   - Metin özgün, tarihsel gerçekliklere sadık ve edebi dili güçlü olmalıdır.
   - Bağlam yalnızca bir dekor olmamalı, sorulan sorunun cevabı mutlaka bu metnin okunup anlaşılmasına bağlı olmalıdır (bkz. Adım 5 — İşlevsellik Testi).

2. **Soru Kökü:**
   - Kazanımda hedeflenen beceriyi (analiz, çıkarım, tarihsel empati, karşılaştırma vb.) doğrudan ölçmelidir.
   - "...yargılardan hangisine ulaşılabilir / ulaşılamaz?" veya "...aşağıdakilerden hangisi gösterilebilir / gösterilemez?" şeklinde net olmalıdır.
   - Çift olumsuzluk ve öznel ifadelerden kaçınılmalı (bkz. Adım 3).
{coktan_secmeli_blok if "Çoktan Seçmeli" in soru_tipi or "ÖSYM" in soru_tipi else ""}{acik_uclu_blok if "Açık Uçlu" in soru_tipi or "Klasik" in soru_tipi else ""}{baglam_temelli_blok if baglam_temelli_mi else ""}
6. **Genel Kalite Kriterleri:**
   - Sorular birbirini tekrar etmemeli, her biri farklı bir alt beceriyi veya bakış açısını ölçmelidir.
   - Tarihsel doğruluk esastır; kurgusal ama tarihe sadık bağlam metinleri kullanılabilir (kaynak materyal yüklenmişse yukarıdaki zorunlu kurala uy).
   - Metin insan bir eğitimci tarafından yazılmış doğallıkta olmalı; yapay zekâ üslubu, klişe kalıplar ve tekdüze cümle yapıları kullanılmamalıdır (bkz. madde 0).

### ⏱️ ÇIKTI UZUNLUĞU YÖNETİMİ (ZORUNLU):
İstenen soru sayısını tamamlamak, açıklamaları uzatmaktan HER ZAMAN daha önceliklidir. Eğer yer/uzunluk kısıtı hissedersen:
1. Önce çözüm açıklamalarını kısalt (her seçenek için 1-2 cümle yeterlidir, uzun paragraflara gerek yok).
2. Bağlam metnini gereksiz yere uzatma; 2 paragraf kuralına sadık kal, fazladan süsleme ekleme.
3. Asla son soruyu yarım bırakma veya istenen sayıdan daha azını üretip bitirme; gerekirse tüm sorular için açıklamaları daha da sadeleştir ama SAYIYI TAMAMLA.

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
        min_value=1, max_value=20, value=1, step=1,
        help="Bağlam Temelli seçiliyse, aynı bağlama dayalı en az 5 soru otomatik olarak istenir."
    )
    if "Bağlam Temelli" in soru_tipi and soru_sayisi < 5:
        st.caption("ℹ️ Bağlam temelli sorularda ÖSYM/TYMM mantığı gereği aynı metne dayalı en az 5 soru istenecektir.")
    if soru_sayisi > 10:
        st.caption("⚠️ 10'un üzerindeki sayılarda model çıktı (token) sınırına takılıp yarım kalabilir. Önerimiz: büyük setleri 8-10'luk gruplar hâlinde ayrı ayrı ürettirmeniz.")

    st.divider()
    st.header("🏷️ Odak Kavramlar (İsteğe Bağlı)")
    odak_kavramlar = st.multiselect(
        "Soruda özellikle vurgulanmasını istediğiniz kavramları seçin:",
        options=MUFREDAT_11_SINIF[unite_secimi]["kavramlar"]
    )

    st.divider()
    st.header("🤖 AI ile Doğrudan Üretim")

    saglayici = st.radio(
        "AI Sağlayıcısı:",
        options=["Anthropic (Claude)", "Google (Gemini)"],
        horizontal=True
    )

    if saglayici == "Anthropic (Claude)":
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
    else:
        if not GEMINI_MEVCUT:
            st.warning("`google-generativeai` paketi kurulu değil. Kurmak için: `pip install google-generativeai`")
        api_key = st.text_input(
            "Google Gemini API Anahtarı:",
            type="password",
            help="Anahtarınız yalnızca bu oturumda kullanılır, hiçbir yerde saklanmaz. Google AI Studio üzerinden alabilirsiniz."
        )
        model_secimi = st.selectbox(
            "Model:",
            options=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
            index=0,
            help="Güncel model listesi Google tarafından değişebilir; ai.google.dev üzerinden kontrol edip gerekirse buradaki değerleri güncelleyin."
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

# ---- Kaynak Kitap / Doküman Kütüphanesi ----
st.subheader("📚 Kaynak Kitap / Doküman Kütüphanesi")
st.caption("İstediğiniz kadar PDF veya metin (.txt) dosyası yükleyebilirsiniz. Birden fazla yükleme işlemiyle bir kütüphane oluşturabilir, dilediğiniz dosyayı listeden çıkarabilirsiniz. Yüklenen içerik, soru üretiminde birincil kaynak olarak kullanılır.")

yeni_dosyalar = st.file_uploader(
    "Kitap / ders notu / kaynak PDF ya da metin dosyalarını sürükleyip bırakın:",
    type=["pdf", "txt"],
    accept_multiple_files=True,
    help="Taranmış (görsel) PDF'lerden metin çıkarılamayabilir; bu durumda dosyayı önce OCR'dan geçirmeniz gerekir.",
    key="kutuphane_yukleyici"
)

st.caption(f"📁 Dosyalar bu bilgisayarda kalıcı olarak şurada saklanır: `{KUTUPHANE_KLASORU}`")

maks_kaynak_karakter = st.slider(
    "Modele gönderilecek azami kaynak metni (karakter):",
    min_value=20000, max_value=800000, value=MAKS_KAYNAK_KARAKTER_VARSAYILAN, step=10000,
    help="Kütüphanedeki metin bu sınırı aşarsa yalnızca ilk N karakter modele gönderilir. Kaba tahmin: 1 token ≈ 4 karakter "
         "(150.000 karakter ≈ 35-40 bin token). Çok yüksek değerler API maliyetini ve yanıt süresini artırır; "
         "kullandığınız modelin bağlam penceresini (context window) aşmadığından emin olun."
)

col_yukle, col_temizle = st.columns([1, 1])
with col_yukle:
    if st.button("➕ Yüklenen Dosyaları Kütüphaneye Kaydet", use_container_width=True, disabled=not yeni_dosyalar):
        with st.spinner("Dosyalar diske kaydediliyor..."):
            yuklenen_dosyalari_isle(yeni_dosyalar)
            st.session_state.kaynak_metin, st.session_state.kaynak_dosya_adlari = kutuphaneyi_diskten_yukle()
        st.success(f"{len(yeni_dosyalar)} dosya kalıcı olarak kaydedildi.")
        st.rerun()

with col_temizle:
    if st.button("🗑️ Kütüphaneyi Tamamen Temizle (Diskten Sil)", use_container_width=True, disabled=not st.session_state.kaynak_dosya_adlari):
        for dosya_yolu in KUTUPHANE_KLASORU.glob("*"):
            dosya_yolu.unlink(missing_ok=True)
        st.session_state.kaynak_metin = ""
        st.session_state.kaynak_dosya_adlari = []
        st.success("Kütüphane diskten tamamen silindi.")
        st.rerun()

if st.session_state.kaynak_dosya_adlari:
    toplam_karakter = len(st.session_state.kaynak_metin)
    st.write(f"**Kütüphanedeki dosyalar ({len(st.session_state.kaynak_dosya_adlari)} adet, toplam ~{toplam_karakter:,} karakter):**")
    for i, ad in enumerate(st.session_state.kaynak_dosya_adlari):
        c1, c2 = st.columns([5, 1])
        c1.write(f"📄 {ad}")
        if c2.button("Kaldır", key=f"kaldir_{i}"):
            (KUTUPHANE_KLASORU / ad).unlink(missing_ok=True)
            st.session_state.kaynak_metin, st.session_state.kaynak_dosya_adlari = kutuphaneyi_diskten_yukle()
            st.rerun()

    if toplam_karakter > maks_kaynak_karakter:
        st.warning(
            f"Kütüphane {toplam_karakter:,} karakter içeriyor; prompt şişmesini önlemek için modele gönderilirken "
            f"yalnızca ilk {maks_kaynak_karakter:,} karakter kullanılacaktır. Yukarıdaki kaydırıcıdan bu sınırı "
            f"yükseltebilir veya ilgili kısmı 'Özel Bağlam Notu' alanına özetleyerek belirtebilirsiniz."
        )

    with st.expander("Kütüphane içeriğini önizle"):
        st.text(st.session_state.kaynak_metin[:3000] + ("..." if len(st.session_state.kaynak_metin) > 3000 else ""))
else:
    st.caption("Henüz kütüphaneye dosya eklenmedi. Dosya yüklenmezse sorular genel tarih bilginizle kurgusal olarak üretilir.")

st.divider()

# ---- Prompt Üretme ve Gösterim Alanı ----
st.subheader("🚀 Yapay Zeka Soru Üretim Promptu")

generated_prompt = build_prompt(
    unite_secimi, kazanim_kodu, kazanim_tanimi, soru_tipi, zorluk,
    odak_kavramlar, ek_baglam, soru_sayisi,
    kaynak_metin=st.session_state.kaynak_metin[:maks_kaynak_karakter]
)

st.text_area(
    "Aşağıdaki promptu LLM (Claude, ChatGPT, Gemini) modeline yapıştırarak sorunuzu üretebilirsiniz:",
    value=generated_prompt,
    height=320
)

col_btn0, col_btn1, col_btn2, col_btn3 = st.columns(4)

with col_btn0:
    uret_tiklandi = st.button(
        "✨ Soruyu Şimdi Üret",
        use_container_width=True,
        type="primary",
        disabled=not (ANTHROPIC_MEVCUT or GEMINI_MEVCUT)
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
        "kaynak_dosyalar": st.session_state.kaynak_dosya_adlari,
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
    if saglayici == "Anthropic (Claude)" and not ANTHROPIC_MEVCUT:
        st.error("`anthropic` paketi kurulu değil. Terminalde `pip install anthropic` çalıştırıp uygulamayı yeniden başlatın.")
    elif saglayici == "Google (Gemini)" and not GEMINI_MEVCUT:
        st.error("`google-generativeai` paketi kurulu değil. Terminalde `pip install google-generativeai` çalıştırıp uygulamayı yeniden başlatın.")
    elif not api_key:
        st.error(f"Lütfen sol menüden {saglayici} API anahtarınızı girin.")
    else:
        with st.spinner("Soru üretiliyor, lütfen bekleyin..."):
            try:
                if saglayici == "Anthropic (Claude)":
                    st.session_state.uretilen_soru = soru_uret_api(api_key, model_secimi, generated_prompt)
                else:
                    st.session_state.uretilen_soru = soru_uret_gemini(api_key, model_secimi, generated_prompt)
            except Exception as e:
                if ANTHROPIC_MEVCUT and isinstance(e, anthropic.AuthenticationError):
                    st.error("API anahtarı geçersiz görünüyor. Lütfen kontrol edip tekrar deneyin.")
                elif ANTHROPIC_MEVCUT and isinstance(e, anthropic.APIStatusError):
                    st.error(f"API hatası: {e}")
                else:
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
