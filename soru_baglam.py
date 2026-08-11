import io
import json
import pandas as pd
import pypdf
import streamlit as st
import google.generativeai as genai

# --- Sayfa Yapılandırması ---
st.set_page_config(
    page_title="11. Sınıf Tarih - Bağlam Temelli Soru Üreteci",
    page_icon="📜",
    layout="wide"
)

# --- Yardımcı Fonksiyonlar ---

def extract_text_from_pdf(pdf_file) -> str:
    """Yüklenen PDF dosyasından metin içeriklerini çıkarır."""
    text = ""
    try:
        pdf_reader = pypdf.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        st.error(f"PDF okunurken bir hata oluştu: {e}")
    return text

def build_system_prompt(guideline_text: str) -> str:
    """Soru yazım kılavuzunu içeren sistem yönergesini oluşturur."""
    prompt = f"""
Sen YKS (ÖSYMS tarzı) ve MEB müfredatına uygun, 11. Sınıf Tarih dersi için bağlam temelli (paragrafa/kaynağa dayalı) yüksek kaliteli sorular hazırlayan uzman bir ölçme ve değerlendirme uzmanısın.

Aşağıda verilen Soru Hazırlama Kılavuzu'ndaki ilkelere KESİNLİKLE uymalısın:

=== SORU HAZIRLAMA KILAVUZU ===
{guideline_text}
================================

Soru Üretim Kuralları:
1. Her soru seti 1 adet kapsayıcı ve özgün Bağlam Metni (köken metin, harita/tarihçi yorumu veya tarihsel belge niteliğinde) içermelidir.
2. Bu bağlam metnine bağlı tam 3 veya 4 adet çoktan seçmeli soru oluşturulmalıdır.
3. Her soru kesinlikle 5 seçenekli olmalıdır (A, B, C, D, E).
4. Sorular doğrudan bilgi ezberini değil; analiz, sentez, kronolojik kavrayış, neden-sonuç ilişkisi ve tarihsel empati gibi üst düzey bilişsel becerileri ölçmelidir.
5. Verilen öğrenme çıktıları (kazanımlar) ve ders kitabı metni dışına çıkılmamalıdır.
6. Yanıt formatın KESİNLİKLE geçerli bir JSON objesi olmalıdır. Ekstra açıklama veya markdown yazısı ekleme.
"""
    return prompt

def get_working_model(api_key: str, system_prompt: str):
    """API anahtarının erişebildiği aktif Gemini modelini otomatik tespit eder."""
    genai.configure(api_key=api_key)
    
    # Öncelikli denenecek model isimleri
    candidate_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "gemini-1.0-pro"
    ]
    
    # 1. Aşama: Aday modelleri sırayla dene
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return model
        except Exception:
            continue

    # 2. Aşama: Dinamik olarak hesaptaki modelleri listele ve metin üretebilen ilk modeli seç
    try:
        available_models = genai.list_models()
        for m in available_models:
            if "generateContent" in m.supported_generation_methods:
                model = genai.GenerativeModel(
                    model_name=m.name,
                    system_instruction=system_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                return model
    except Exception as e:
        st.error(f"Aktif model tespit edilirken hata oluştu: {e}")
        
    # Varsayılan son çare
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
        generation_config={"response_mime_type": "application/json"}
    )

def generate_questions(
    api_key: str,
    system_prompt: str,
    book_text: str,
    outcomes: str,
    num_contexts: int
) -> list:
    """Gemini API kullanarak bağlam temelli soruları üretir."""
    
    # JSON Çıktı Şablonu Yönergesi
    json_structure_instruction = """
Üreteceğin JSON yapısı şu formatta olmalıdır:
{
  "baglam_setleri": [
    {
      "baglam_id": 1,
      "baglam_metni": "Bağlam metni buraya gelecek...",
      "sorular": [
        {
          "soru_no": 1,
          "soru_kok": "Soru kökü buraya...",
          "secenekler": {
            "A": "Seçenek A",
            "B": "Seçenek B",
            "C": "Seçenek C",
            "D": "Seçenek D",
            "E": "Seçenek E"
          },
          "dogru_cevap": "A",
          "cozum_aciklamasi": "Çözüm açıklaması..."
        }
      ]
    }
  ]
}
"""

    user_message = f"""
Aşağıdaki ders kitabı içeriğini ve öğrenme çıktılarını kullanarak {num_contexts} adet bağlam seti (her bağlamda 3-4 soru olacak şekilde) oluştur.

=== ÖĞRENME ÇIKTILARI / KAZANIMLAR ===
{outcomes}

=== DERS KİTABI METIN BÖLÜMÜ ===
{book_text[:15000]}  # Token sınırını korumak için metin kesiti

Lütfen kılavuza tam uyarak yukarıda belirtilen JSON formatında yanıt ver.
"""

    # Dinamik model tespiti ile model çağrısı yapılıyor
    model = get_working_model(api_key, system_prompt)

    response = model.generate_content(user_message + "\n\n" + json_structure_instruction)
    
    try:
        data = json.loads(response.text)
        return data.get("baglam_setleri", [])
    except Exception as e:
        st.error(f"JSON yanıtı ayrıştırılamadı: {e}")
        st.text(response.text)
        return []

# --- Arayüz Tasarımı ---

st.title("📜 11. Sınıf Tarih Ders Kitabı - Bağlam Temelli Soru Üreteci")
st.markdown("ÖSYM ve MEB standartlarında, kaynak metne dayalı 5 seçenekli soru bankası oluşturma araci.")

st.sidebar.header("⚙️ Ayarlar ve API")

# API Key kontrolü
user_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

if user_api_key:
    api_key = user_api_key
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = ""

st.sidebar.header("📁 Dosya ve Veri Yükleme")
guideline_file = st.sidebar.file_uploader("Soru Yazım Kılavuzu (PDF)", type=["pdf"])
book_file = st.sidebar.file_uploader("Tarih Ders Kitabı / Metni (PDF)", type=["pdf"])

num_contexts = st.sidebar.number_input("Üretilecek Bağlam Seti Sayısı", min_value=1, max_value=5, value=1)

st.header("🎯 Öğrenme Çıktıları (Kazanımlar)")
learning_outcomes = st.text_area(
    "Soruların odaklanacağı müfredat kazanımlarını buraya giriniz:",
    height=150,
    placeholder="Örn: 11.1.2. Osmanlı Devleti'nin batı karşısındaki askeri ve diplomatik üstünlüğünü kaybetmesinin nedenlerini analiz eder."
)

if st.button("🚀 Bağlam Temelli Soruları Üret", type="primary"):
    if not api_key:
        st.warning("Lütfen sol menüden Gemini API anahtarınızı giriniz veya Secrets alanına ekleyiniz.")
    elif not guideline_file:
        st.warning("Lütfen Soru Yazım Kılavuzu PDF dosyasını yükleyiniz.")
    elif not book_file:
        st.warning("Lütfen Tarih Ders Kitabı PDF dosyasını yükleyiniz.")
    elif not learning_outcomes.strip():
        st.warning("Lütfen en az bir öğrenme çıktısı/kazanım giriniz.")
    else:
        with st.spinner("PDF dosyaları taranıyor ve metinler ayıklanıyor..."):
            guideline_text = extract_text_from_pdf(guideline_file)
            book_text = extract_text_from_pdf(book_file)
            
        with st.spinner("Soru yazım kılavuzu ışığında bağlam temelli sorular üretiliyor..."):
            system_prompt = build_system_prompt(guideline_text)
            results = generate_questions(
                api_key=api_key,
                system_prompt=system_prompt,
                book_text=book_text,
                outcomes=learning_outcomes,
                num_contexts=num_contexts
            )
            
            if results:
                st.success(f"Başarıyla {len(results)} adet bağlam seti üretildi!")
                st.session_state["generated_results"] = results

# --- Üretilen Soruların Görüntülenmesi ve Dışa Aktarılması ---

if "generated_results" in st.session_state and st.session_state["generated_results"]:
    results = st.session_state["generated_results"]
    
    st.divider()
    st.header("📑 Üretilen Soru Setleri")
    
    for b_idx, baglam in enumerate(results, 1):
        with st.expander(f"📌 Bağlam Seti #{b_idx}", expanded=True):
            st.subheader("📖 Bağlam Metni")
            st.info(baglam.get("baglam_metni", ""))
            
            st.markdown("---")
            st.subheader("❓ Bağlı Sorular")
            
            for q in baglam.get("sorular", []):
                st.markdown(f"**Soru {q.get('soru_no')}:** {q.get('soru_kok')}")
                secenekler = q.get("secenekler", {})
                for key in ["A", "B", "C", "D", "E"]:
                    st.write(f"**{key})** {secenekler.get(key, '')}")
                
                with st.popover(f"Soru {q.get('soru_no')} Doğru Cevap ve Çözümü"):
                    st.write(f"**Doğru Cevap:** {q.get('dogru_cevap')}")
                    st.write(f"**Çözüm Açıklaması:** {q.get('cozum_aciklamasi')}")
                st.write("")

    # JSON İndirme Butonu
    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 Soruları JSON Olarak İndir",
        data=json_str,
        file_name="baglam_temelli_tarih_sorulari.json",
        mime="application/json"
    )
