import io
import json
import pandas as pd
import pypdf
import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

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

def build_system_prompt(guideline_text: str, difficulty: str) -> str:
    """Soru yazım kılavuzunu ve seçilen zorluk seviyesini içeren sistem yönergesini oluşturur."""
    prompt = f"""
Sen YKS (ÖSYM tarzı) ve MEB müfredatına uygun, 11. Sınıf Tarih dersi için bağlam temelli (paragrafa/kaynağa dayalı) yüksek kaliteli sorular hazırlayan uzman bir ölçme ve değerlendirme uzmanısın.

Aşağıda verilen Soru Hazırlama Kılavuzu'ndaki ilkelere KESİNLİKLE uymalısın:

=== SORU HAZIRLAMA KILAVUZU ===
{guideline_text}
================================

Soru Üretim Kuralları:
1. Her soru seti 1 adet kapsayıcı ve özgün Bağlam Metni (köken metin, harita/tarihçi yorumu veya tarihsel belge niteliğinde) içermelidir.
2. Bu bağlam metnine bağlı tam 3 veya 4 adet çoktan seçmeli soru oluşturulmalıdır.
3. Her soru kesinlikle 5 seçenekli olmalıdır (A, B, C, D, E).
4. Soruların hedef zorluk seviyesi KESİNLİKLE '{difficulty.upper()}' seviyesinde olmalıdır.
   - Kolay: Doğrudan bağlamdan çıkarılabilen, temel kavrayış ve ilişkilendirme ölçen sorular.
   - Orta: Analiz, neden-sonuç kurma, kronolojik kavrayış ve çıkarım yapmayı gerektiren sorular.
   - Zor: Üst düzey sentez, kavramsal derinlik, çeldiricileri güçlü ve çok yönlü tarihsel yorumlama gerektiren sorular.
5. Verilen öğrenme çıktıları (kazanımlar) ve ders kitabı metni dışına çıkılmamalıdır.
6. Ürettiğin her bağlam seti için soruların akademik niteliğini, çeldirici gücünü ve kılavuza uyumunu değerlendiren 0-100 arası bir 'kalite_skoru' ve bunun gerekçesini belirten bir 'kalite_degerlendirmesi' eklemelisin.
7. Yanıt formatın KESİNLİKLE geçerli bir JSON objesi olmalıdır. Ekstra açıklama veya markdown yazısı ekleme.
"""
    return prompt

def create_word_document(results: list) -> io.BytesIO:
    """Üretilen soru setlerini şık ve düzenli bir Word (.docx) belgesine dönüştürür."""
    doc = Document()
    
    # Başlık Alanı
    title = doc.add_heading("11. Sınıf Tarih - Bağlam Temelli Soru Bankası", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle = doc.add_paragraph("ÖSYM / MEB Standartlarında Hazırlanmış Bağlam Temelli Sorular")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    for b_idx, baglam in enumerate(results, 1):
        # Bağlam Başlığı ve Metrikler
        h1 = doc.add_heading(f"BAĞLAM SETİ #{b_idx}", level=1)
        
        info_p = doc.add_paragraph()
        info_p.add_run(f"Zorluk Seviyesi: ").bold = True
        info_p.add_run(f"{baglam.get('zorluk_seviyesi', 'Belirtilmedi')} | ")
        info_p.add_run(f"Kalite Skoru: ").bold = True
        info_p.add_run(f"{baglam.get('kalite_skoru', 85)}/100\n")
        info_p.add_run(f"Kalite Değerlendirmesi: ").bold = True
        info_p.add_run(f"{baglam.get('kalite_degerlendirmesi', '')}")
        
        # Bağlam Metni
        doc.add_heading("📖 Bağlam Metni", level=2)
        p_baglam = doc.add_paragraph(baglam.get("baglam_metni", ""))
        p_baglam.paragraph_format.left_indent = Inches(0.25)
        p_baglam.paragraph_format.right_indent = Inches(0.25)
        
        # Sorular
        doc.add_heading("❓ Sorular", level=2)
        for q in baglam.get("sorular", []):
            q_p = doc.add_paragraph()
            q_p.add_run(f"Soru {q.get('soru_no')}: ").bold = True
            q_p.add_run(q.get("soru_kok", ""))
            
            secenekler = q.get("secenekler", {})
            for key in ["A", "B", "C", "D", "E"]:
                opt_p = doc.add_paragraph()
                opt_p.paragraph_format.left_indent = Inches(0.4)
                opt_p.add_run(f"{key}) ").bold = True
                opt_p.add_run(secenekler.get(key, ""))
            
            doc.add_paragraph() # Sorular arası boşluk
            
        doc.add_page_break()

    # Cevap Anahtarı Sayfası
    doc.add_heading("🔑 CEVAP ANAHTARI VE ÇÖZÜM AÇIKLAMALARI", level=1)
    
    for b_idx, baglam in enumerate(results, 1):
        doc.add_heading(f"Bağlam Seti #{b_idx} Cevapları", level=2)
        for q in baglam.get("sorular", []):
            ans_p = doc.add_paragraph()
            ans_p.add_run(f"Soru {q.get('soru_no')} Doğru Cevap: ").bold = True
            ans_p.add_run(f"{q.get('dogru_cevap')}\n")
            ans_p.add_run(f"Çözüm Açıklaması: ").bold = True
            ans_p.add_run(f"{q.get('cozum_aciklamasi')}")
            ans_p.paragraph_format.left_indent = Inches(0.2)
            doc.add_paragraph()

    # Bellekte dosyayı oluştur ve döndür
    target_stream = io.BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    return target_stream

def generate_questions_with_fallback(
    api_key: str,
    system_prompt: str,
    user_message: str
):
    """
    Erişilebilir kararlı modelleri sırayla dener. 404 veya yetki hatası
    veren modelleri atlayarak çalışan ilk modelden yanıt alır.
    """
    genai.configure(api_key=api_key)

    # Öncelikli ve standart çalışması garanti edilen model listesi
    candidate_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro"
    ]

    last_exception = None

    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(user_message)
            return response.text
        except Exception as err:
            last_exception = err
            continue

    # Eğer aday modellerden biri çalışmazsa API'den dinamik liste alıp dene
    try:
        available_models = genai.list_models()
        for m in available_models:
            if "generateContent" in m.supported_generation_methods:
                if "2.5" in m.name:
                    continue
                try:
                    model = genai.GenerativeModel(
                        model_name=m.name,
                        system_instruction=system_prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = model.generate_content(user_message)
                    return response.text
                except Exception as inner_err:
                    last_exception = inner_err
                    continue
    except Exception as list_err:
        pass

    raise last_exception if last_exception else RuntimeError("Erişilebilir bir Gemini modeli bulunamadı.")

def generate_questions(
    api_key: str,
    system_prompt: str,
    book_text: str,
    outcomes: str,
    num_contexts: int,
    difficulty: str
) -> list:
    """Gemini API kullanarak bağlam temelli soruları üretir."""
    
    # JSON Çıktı Şablonu Yönergesi
    json_structure_instruction = """
Üreteceğin JSON yapısı şu formatta olmalıdır:
{
  "baglam_setleri": [
    {
      "baglam_id": 1,
      "zorluk_seviyesi": "Orta",
      "kalite_skoru": 92,
      "kalite_degerlendirmesi": "Bağlam metni zengin, çeldiriciler güçlü ve kazanımla tam uyumlu.",
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

=== HEDEF ZORLUK SEVİYESİ ===
{difficulty}

=== ÖĞRENME ÇIKTILARI / KAZANIMLAR ===
{outcomes}

=== DERS KİTABI METIN BÖLÜMÜ ===
{book_text[:15000]}  # Token sınırını korumak için metin kesiti

Lütfen kılavuza tam uyarak yukarıda belirtilen JSON formatında yanıt ver.

{json_structure_instruction}
"""

    try:
        response_text = generate_questions_with_fallback(api_key, system_prompt, user_message)
        data = json.loads(response_text)
        return data.get("baglam_setleri", [])
        
    except Exception as e:
        st.error(f"Soru üretimi sırasında bir hata oluştu: {e}")
        return []

# --- Arayüz Tasarımı ---

st.title("📜 11. Sınıf Tarih Ders Kitabı - Bağlam Temelli Soru Üreteci")
st.markdown("ÖSYM ve MEB standartlarında, kaynak metne dayalı 5 seçenekli soru bankası oluşturma aracı.")

st.sidebar.header("⚙️ Ayarlar ve API")

# API Key kontrolü
user_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

if user_api_key:
    api_key = user_api_key
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = ""

st.sidebar.header("📊 Soru Parametreleri")

# Zorluk Seviyesi Seçimi
difficulty_option = st.sidebar.selectbox(
    "🎯 Zorluk Seviyesi",
    options=["Kolay", "Orta", "Zor"],
    index=1,
    help="Soruların bilişsel seviyesini ve çeldirici gücünü belirler."
)

num_contexts = st.sidebar.number_input("Üretilecek Bağlam Seti Sayısı", min_value=1, max_value=5, value=1)

st.sidebar.header("📁 Dosya ve Veri Yükleme")
guideline_file = st.sidebar.file_uploader("Soru Yazım Kılavuzu (PDF)", type=["pdf"])

st.sidebar.markdown("---")
st.sidebar.subheader("📚 Tarih Ders Kitabı / Metni")

# PDF Yükleme ve Metin Yapıştırma Sekmeleri
tab_pdf, tab_text = st.sidebar.tabs(["📄 PDF Yükle", "✍️ Metin Yapıştır"])

with tab_pdf:
    book_file = st.file_uploader("Ders Kitabı PDF Dosyası", type=["pdf"])

with tab_text:
    book_pasted_text = st.text_area(
        "Ders Kitabı Metnini Buraya Yapıştırın:",
        height=200,
        placeholder="İlgili ünite veya konu metnini buraya kopyalayıp yapıştırabilirsiniz..."
    )

st.header("🎯 Öğrenme Çıktıları (Kazanımlar)")
learning_outcomes = st.text_area(
    "Soruların odaklanacağı müfredat kazanımlarını buraya giriniz:",
    height=150,
    placeholder="Örn: 11.1.2. Osmanlı Devleti'nin batı karşısındaki askeri ve diplomatik üstünlüğünü kaybetmesinin nedenlerini analiz eder."
)

if st.button("🚀 Bağlam Temelli Soruları Üret", type="primary"):
    # Ders kitabı metninin kaynağını belirleme (PDF veya Yapıştırılan Metin)
    final_book_text = ""
    
    if book_file is not None:
        with st.spinner("PDF dosyası taranıyor ve metin ayıklanıyor..."):
            final_book_text = extract_text_from_pdf(book_file)
    elif book_pasted_text.strip():
        final_book_text = book_pasted_text.strip()

    if not api_key:
        st.warning("Lütfen sol menüden Gemini API anahtarınızı giriniz veya Secrets alanına ekleyiniz.")
    elif not guideline_file:
        st.warning("Lütfen Soru Yazım Kılavuzu PDF dosyasını yükleyiniz.")
    elif not final_book_text:
        st.warning("Lütfen Ders Kitabı PDF dosyasını yükleyin veya metin alanına konu metnini yapıştırın.")
    elif not learning_outcomes.strip():
        st.warning("Lütfen en az bir öğrenme çıktısı/kazanım giriniz.")
    else:
        with st.spinner("Soru Yazım Kılavuzu taranıyor..."):
            guideline_text = extract_text_from_pdf(guideline_file)
            
        with st.spinner(f"{difficulty_option} seviyesinde bağlam temelli sorular üretiliyor ve kalite skoru hesaplanıyor..."):
            system_prompt = build_system_prompt(guideline_text, difficulty_option)
            results = generate_questions(
                api_key=api_key,
                system_prompt=system_prompt,
                book_text=final_book_text,
                outcomes=learning_outcomes,
                num_contexts=num_contexts,
                difficulty=difficulty_option
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
        with st.expander(f"📌 Bağlam Seti #{b_idx} | Zorluk: {baglam.get('zorluk_seviyesi', difficulty_option)}", expanded=True):
            
            # Kalite Skoru ve Metrikler
            score = baglam.get("kalite_skoru", 85)
            evaluation = baglam.get("kalite_degerlendirmesi", "Soru kalitesi standartlara uygun.")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.metric(label="⭐ Kalite Skoru", value=f"{score}/100")
            with col2:
                st.caption("🔍 **Kalite Değerlendirmesi:**")
                st.write(evaluation)
                
            st.markdown("---")
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

    st.divider()
    st.subheader("💾 Dışa Aktarma Seçenekleri")
    
    col_dl1, col_dl2 = st.columns(2)
    
    # Word İndirme Butonu
    with col_dl1:
        doc_file = create_word_document(results)
        st.download_button(
            label="📄 Soruları Word (.docx) Olarak İndir",
            data=doc_file,
            file_name="baglam_temelli_tarih_sorulari.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
        
    # JSON İndirme Butonu
    with col_dl2:
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Soruları JSON Olarak İndir",
            data=json_str,
            file_name="baglam_temelli_tarih_sorulari.json",
            mime="application/json"
        )
