import io
import json
import pandas as pd
import pypdf
import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- Sayfa Yapılandırması ---
st.set_page_config(
    page_title="11. Sınıf Tarih - Çoklu AI Soru Üreteci",
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

def build_system_prompt(guideline_text: str, question_mode: str, exam_type: str, difficulty: str) -> str:
    """Soru yazım kılavuzunu, soru modunu ve zorluk seviyesini içeren sistem yönergesini oluşturur."""
    
    if question_mode == "Klasik ÖSYM (TYT / AYT)":
        mode_instruction = f"""
Soru Tipi: KLASİK ÖSYM TARZI İŞTAKNİ/BAĞIMSIZ SORULAR (Sınav Türü: {exam_type})

Eğer Sınav Türü 'TYT' ise:
- Sorular yorum, nedensellik, tarihsel mantık yürütme, dönem zihniyetini kavrama ve öncüllü (I. II. III.) yapılarda olmalıdır.
- Ezber doğrudan bilgi sorularından kaçınılmalı, öğrencinin tarihsel düşünme becerisi ölçülmelidir.

Eğer Sınav Türü 'AYT' ise:
- Sorular doğrudan terim bilgisi, kronolojik hakimiyet, olay-antlaşma-aktör eşleştirmesi ve alan bilgisi düzeyinde derinlik içermelidir.
- Öncüllü (I. II. III.) veya doğrudan "Hangisi söylenebilir/söylenemez?" tarzı akademik derinliği yüksek sorular olmalıdır.

Her soru birbirinden bağımsız, 5 seçenekli (A, B, C, D, E) olmalı ve son derece GÜÇLÜ ÇELDİRİCİLER barındırmalıdır.
"""
    else:
        mode_instruction = """
Soru Tipi: BAĞLAM TEMELLİ (KAPSAYICI METNE BAĞLI SORU SETLERİ)
1 adet kapsayıcı ve özgün Bağlam Metni oluşturulmalı ve bu metne bağlı 3-4 adet 5 seçenekli soru yazılmalıdır.
"""

    prompt = f"""
Sen YKS (TYT ve AYT derecelendirme seviyesinde) ve MEB müfredatına tam uyumlu, 11. Sınıf Tarih dersi için **üst düzey akademik nitelikte, ÖSYM standartlarında** sorular hazırlayan kıdemli bir Ölçme ve Değerlendirme Uzmanısın.

Aşağıda verilen Soru Hazırlama Kılavuzu'ndaki ilkelere KESİNLİKLE uymalısın:

=== SORU HAZIRLAMA KILAVUZU ===
{guideline_text}
================================

=== SORU MODU VE FORMAT YÖNERGESİ ===
{mode_instruction}

### ZORLUK VE ÇELDİRİCİ STANDARTLARI (KRİTİK):
Soruların hedef zorluk seviyesi KESİNLİKLE '{difficulty.upper()}' seviyesinde olmalıdır.

1. **Sığ Sorulardan Kaçın:** Doğrudan basit metin kopyalaması veya sığ şıklar üretme.
2. **Güçlü ve Tuzaklı Çeldiriciler (A, B, C, D, E):**
   - Çeldiriciler kesinlikle göze çarpan "saçma" veya "kolay elenen" şıklar olmamalıdır.
   - Çeldiricilerin her biri, konu hakkında yüzeysel bilgisi olan bir öğrencinin düşebileceği, tarihsel olarak mantıklı görünen ancak bağlamdaki/sorudaki ince mantık örgüsünü veya zamansal kronolojiyi ıskalayan **güçlü yanıltıcılardan** oluşmalıdır.
3. **Aşırı Titiz Kalite Puanlaması:** Ürettiğin soruları acımasızca eleştir. Gerçekten ÖSYM derecelendirme sorusu niteliğindeyse yüksek puan (90-100) ver, basit kaldıysa puanı düşür ve gerekçesini belirt.
4. Yanıt formatın KESİNLİKLE geçerli bir JSON objesi olmalıdır. Başka hiçbir açıklama veya ön metin yazma.
"""
    return prompt

def generate_with_ai_provider(
    provider: str,
    model_name: str,
    api_key: str,
    system_prompt: str,
    user_message: str
) -> str:
    """Seçilen yapay zeka sağlayıcısına göre istek atarak JSON yanıtını döndürür."""
    
    # 1. GOOGLE GEMINI
    if provider == "Google Gemini":
        genai.configure(api_key=api_key)
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.35,
            "top_p": 0.95
        }
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
            generation_config=generation_config
        )
        response = model.generate_content(user_message)
        return response.text

    # 2. OPENAI (GPT-4o)
    elif provider == "OpenAI":
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.35
        )
        return response.choices[0].message.content

    # 3. DEEPSEEK
    elif provider == "DeepSeek":
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.35
        )
        return response.choices[0].message.content

    # 4. GROQ (Llama 3)
    elif provider == "Groq (Llama 3)":
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.35
        )
        return response.choices[0].message.content

    else:
        raise ValueError("Geçersiz sağlayıcı seçimi.")

def generate_questions(
    provider: str,
    model_name: str,
    api_key: str,
    system_prompt: str,
    book_text: str,
    outcomes: str,
    num_items: int,
    difficulty: str,
    question_mode: str,
    exam_type: str
) -> list:
    """Seçilen AI servisini kullanarak ÖSYM standartlarında soruları üretir."""
    
    if question_mode == "Klasik ÖSYM (TYT / AYT)":
        json_structure_instruction = """
Üreteceğin JSON yapısı KESİNLİKLE kök anahtarı "sorular" olan bir obje olmalıdır:
{
  "sorular": [
    {
      "soru_no": 1,
      "sinav_turu": "TYT",
      "zorluk_seviyesi": "Zor",
      "soru_kok": "Tarihsel öncüller veya metin içeren ÖSYM tarzı soru kökü...",
      "secenekler": {
        "A": "Güçlü çeldirici veya doğru cevap",
        "B": "Güçlü çeldirici veya doğru cevap",
        "C": "Güçlü çeldirici veya doğru cevap",
        "D": "Güçlü çeldirici veya doğru cevap",
        "E": "Güçlü çeldirici veya doğru cevap"
      },
      "dogru_cevap": "A",
      "cozum_aciklamasi": "Detaylı ÖSYM tarzı akademik çözüm gerekçesi..."
    }
  ]
}
"""
        prompt_goal = f"{num_items} adet bağımsız, 5 seçenekli Klasik ÖSYM ({exam_type}) sorusu"
    else:
        json_structure_instruction = """
Üreteceğin JSON yapısı KESİNLİKLE kök anahtarı "baglam_setleri" olan bir obje olmalıdır:
{
  "baglam_setleri": [
    {
      "baglam_id": 1,
      "zorluk_seviyesi": "Zor",
      "kalite_skoru": 95,
      "kalite_degerlendirmesi": "Açıklama...",
      "baglam_metni": "Bağlam metni...",
      "sorular": [
        {
          "soru_no": 1,
          "soru_kok": "Soru kökü...",
          "secenekler": {
            "A": "A şıkkı",
            "B": "B şıkkı",
            "C": "C şıkkı",
            "D": "D şıkkı",
            "E": "E şıkkı"
          },
          "dogru_cevap": "A",
          "cozum_aciklamasi": "Açıklama..."
        }
      ]
    }
  ]
}
"""
        prompt_goal = f"{num_items} adet Bağlam Seti (her bağlamda 3-4 soru)"

    user_message = f"""
Aşağıdaki ders kitabı içeriğini ve öğrenme çıktılarını kullanarak {prompt_goal} oluştur.

=== HEDEF ZORLUK SEVİYESİ ===
{difficulty}

=== ÖĞRENME ÇIKTILARI / KAZANIMLAR ===
{outcomes}

=== DERS KİTABI METIN BÖLÜMÜ ===
{book_text[:18000]}

Lütfen belirlenen üst düzey zorluk ve güçlü çeldirici standartlarına KESİNLİKLE uyarak yukarıdaki JSON formatında yanıt ver.

{json_structure_instruction}
"""

    try:
        response_text = generate_with_ai_provider(provider, model_name, api_key, system_prompt, user_message)
        data = json.loads(response_text)
        
        target_key = "sorular" if question_mode == "Klasik ÖSYM (TYT / AYT)" else "baglam_setleri"
        
        if isinstance(data, dict):
            return data.get(target_key, [])
        elif isinstance(data, list):
            return data
        else:
            st.error("Model beklenmeyen bir JSON veri yapısı döndürdü.")
            return []
        
    except Exception as e:
        st.error(f"{provider} ile soru üretimi sırasında bir hata oluştu: {e}")
        return []

def create_word_document(results: list, question_mode: str) -> io.BytesIO:
    """Üretilen soru setlerini şık ve düzenli bir Word (.docx) belgesine dönüştürür."""
    doc = Document()
    
    title_text = "11. Sınıf Tarih - ÖSYM Soru Bankası"
    title = doc.add_heading(title_text, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle = doc.add_paragraph(f"Mod: {question_mode} | ÖSYM Standartlarında Hazırlanmış Sorular")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    for b_idx, item in enumerate(results, 1):
        if question_mode == "Klasik ÖSYM (TYT / AYT)":
            doc.add_heading(f"SORU #{b_idx}", level=1)
            
            info_p = doc.add_paragraph()
            info_p.add_run(f"Zorluk Seviyesi: ").bold = True
            info_p.add_run(f"{item.get('zorluk_seviyesi', 'Zor')} | ")
            info_p.add_run(f"Sınav Türü: ").bold = True
            info_p.add_run(f"{item.get('sinav_turu', 'TYT/AYT')}\n")
            
            q_p = doc.add_paragraph()
            q_p.add_run(item.get("soru_kok", ""))
            
            secenekler = item.get("secenekler", {})
            for key in ["A", "B", "C", "D", "E"]:
                opt_p = doc.add_paragraph()
                opt_p.paragraph_format.left_indent = Inches(0.4)
                opt_p.add_run(f"{key}) ").bold = True
                opt_p.add_run(secenekler.get(key, ""))
            
            doc.add_paragraph()
        else:
            doc.add_heading(f"BAĞLAM SETİ #{b_idx}", level=1)
            
            info_p = doc.add_paragraph()
            info_p.add_run(f"Zorluk Seviyesi: ").bold = True
            info_p.add_run(f"{item.get('zorluk_seviyesi', 'Belirtilmedi')} | ")
            info_p.add_run(f"Kalite Skoru: ").bold = True
            info_p.add_run(f"{item.get('kalite_skoru', 85)}/100\n")
            
            doc.add_heading("📖 Bağlam Metni", level=2)
            p_baglam = doc.add_paragraph(item.get("baglam_metni", ""))
            p_baglam.paragraph_format.left_indent = Inches(0.25)
            p_baglam.paragraph_format.right_indent = Inches(0.25)
            
            doc.add_heading("❓ Sorular", level=2)
            for q in item.get("sorular", []):
                q_p = doc.add_paragraph()
                q_p.add_run(f"Soru {q.get('soru_no')}: ").bold = True
                q_p.add_run(q.get("soru_kok", ""))
                
                secenekler = q.get("secenekler", {})
                for key in ["A", "B", "C", "D", "E"]:
                    opt_p = doc.add_paragraph()
                    opt_p.paragraph_format.left_indent = Inches(0.4)
                    opt_p.add_run(f"{key}) ").bold = True
                    opt_p.add_run(secenekler.get(key, ""))
                
                doc.add_paragraph()
            
            doc.add_page_break()

    # Cevap Anahtarı Sayfası
    doc.add_heading("🔑 CEVAP ANAHTARI VE ÇÖZÜM AÇIKLAMALARI", level=1)
    
    if question_mode == "Klasik ÖSYM (TYT / AYT)":
        for b_idx, item in enumerate(results, 1):
            ans_p = doc.add_paragraph()
            ans_p.add_run(f"Soru #{b_idx} Doğru Cevap: ").bold = True
            ans_p.add_run(f"{item.get('dogru_cevap')}\n")
            ans_p.add_run(f"Çözüm Açıklaması: ").bold = True
            ans_p.add_run(f"{item.get('cozum_aciklamasi')}")
            ans_p.paragraph_format.left_indent = Inches(0.2)
            doc.add_paragraph()
    else:
        for b_idx, item in enumerate(results, 1):
            doc.add_heading(f"Bağlam Seti #{b_idx} Cevapları", level=2)
            for q in item.get("sorular", []):
                ans_p = doc.add_paragraph()
                ans_p.add_run(f"Soru {q.get('soru_no')} Doğru Cevap: ").bold = True
                ans_p.add_run(f"{q.get('dogru_cevap')}\n")
                ans_p.add_run(f"Çözüm Açıklaması: ").bold = True
                ans_p.add_run(f"{q.get('cozum_aciklamasi')}")
                ans_p.paragraph_format.left_indent = Inches(0.2)
                doc.add_paragraph()

    target_stream = io.BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    return target_stream

# --- Arayüz Tasarımı ---

st.title("📜 11. Sınıf Tarih - Çoklu AI Destekli ÖSYM Soru Üreteci")
st.markdown("ÖSYM ve MEB standartlarında, tercih edeceğiniz Yapay Zeka servisi ile 5 seçenekli yüksek kaliteli sorular üretin.")

st.sidebar.header("🤖 Yapay Zeka Servis Seçimi")

# Model ve Sağlayıcı Seçimi
ai_provider = st.sidebar.selectbox(
    "Sağlayıcı Seçiniz",
    options=["Google Gemini", "DeepSeek", "OpenAI", "Groq (Llama 3)"]
)

# Seçilen sağlayıcıya göre model listesi ve API Key alanı
if ai_provider == "Google Gemini":
    model_name = st.sidebar.selectbox("Model", ["gemini-1.5-pro", "gemini-2.0-flash", "gemini-1.5-flash"])
    secret_key_name = "GEMINI_API_KEY"
elif ai_provider == "DeepSeek":
    model_name = st.sidebar.selectbox("Model", ["deepseek-chat", "deepseek-coder"])
    secret_key_name = "DEEPSEEK_API_KEY"
elif ai_provider == "OpenAI":
    model_name = st.sidebar.selectbox("Model", ["gpt-4o", "gpt-4o-mini"])
    secret_key_name = "OPENAI_API_KEY"
elif ai_provider == "Groq (Llama 3)":
    model_name = st.sidebar.selectbox("Model", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])
    secret_key_name = "GROQ_API_KEY"

user_api_key = st.sidebar.text_input(f"{ai_provider} API Key", type="password")

if user_api_key:
    api_key = user_api_key
elif secret_key_name in st.secrets:
    api_key = st.secrets[secret_key_name]
else:
    api_key = ""

st.sidebar.header("📊 Soru Parametreleri")

# Soru Modu Seçimi
question_mode = st.sidebar.radio(
    "🧩 Soru Modu Seçin",
    options=["Klasik ÖSYM (TYT / AYT)", "Bağlam Temelli Setler"],
    help="Klasik ÖSYM modu bağımsız sorular üretir; Bağlam Temelli modu bir metne bağlı soru setleri üretir."
)

exam_type = "TYT"
if question_mode == "Klasik ÖSYM (TYT / AYT)":
    exam_type = st.sidebar.selectbox("🏛️ Sınav Türü", options=["TYT (Yorum/Öncüllü)", "AYT (Bilgi/Analiz)", "Karma (TYT + AYT)"])

# Zorluk Seviyesi Seçimi
difficulty_option = st.sidebar.selectbox(
    "🎯 Zorluk Seviyesi",
    options=["Kolay", "Orta", "Zor"],
    index=2,
    help="Soruların bilişsel seviyesini ve çeldirici gücünü belirler."
)

input_label = "Üretilecek Soru Sayısı" if question_mode == "Klasik ÖSYM (TYT / AYT)" else "Üretilecek Bağlam Seti Sayısı"
num_items = st.sidebar.number_input(input_label, min_value=1, max_value=10, value=3 if question_mode == "Klasik ÖSYM (TYT / AYT)" else 1)

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

if st.button("🚀 ÖSYM Standartlarında Soruları Üret", type="primary"):
    final_book_text = ""
    
    if book_file is not None:
        with st.spinner("PDF dosyası taranıyor ve metin ayıklanıyor..."):
            final_book_text = extract_text_from_pdf(book_file)
    elif book_pasted_text.strip():
        final_book_text = book_pasted_text.strip()

    if not api_key:
        st.warning(f"Lütfen sol menüden {ai_provider} API anahtarınızı giriniz veya Secrets alanına ekleyiniz.")
    elif not guideline_file:
        st.warning("Lütfen Soru Yazım Kılavuzu PDF dosyasını yükleyiniz.")
    elif not final_book_text:
        st.warning("Lütfen Ders Kitabı PDF dosyasını yükleyin veya metin alanına konu metnini yapıştırın.")
    elif not learning_outcomes.strip():
        st.warning("Lütfen en az bir öğrenme çıktısı/kazanım giriniz.")
    else:
        with st.spinner("Soru Yazım Kılavuzu taranıyor..."):
            guideline_text = extract_text_from_pdf(guideline_file)
            
        with st.spinner(f"{ai_provider} ({model_name}) kullanılarak {difficulty_option} seviyesinde {question_mode} soruları üretiliyor..."):
            system_prompt = build_system_prompt(guideline_text, question_mode, exam_type, difficulty_option)
            results = generate_questions(
                provider=ai_provider,
                model_name=model_name,
                api_key=api_key,
                system_prompt=system_prompt,
                book_text=final_book_text,
                outcomes=learning_outcomes,
                num_items=num_items,
                difficulty=difficulty_option,
                question_mode=question_mode,
                exam_type=exam_type
            )
            
            if results:
                st.success(f"Başarıyla {len(results)} adet yüksek kaliteli soru/set üretildi!")
                st.session_state["generated_results"] = results
                st.session_state["active_mode"] = question_mode

# --- Üretilen Soruların Görüntülenmesi ve Dışa Aktarılması ---

if "generated_results" in st.session_state and st.session_state["generated_results"]:
    results = st.session_state["generated_results"]
    active_mode = st.session_state.get("active_mode", question_mode)
    
    st.divider()
    st.header("📑 Üretilen ÖSYM Soruları")
    
    if active_mode == "Klasik ÖSYM (TYT / AYT)":
        for idx, q in enumerate(results, 1):
            with st.expander(f"📌 Soru #{idx} | Sınav: {q.get('sinav_turu', 'TYT/AYT')} | Zorluk: {q.get('zorluk_seviyesi', difficulty_option)}", expanded=True):
                st.markdown(f"**Soru {idx}:**\n{q.get('soru_kok')}")
                st.write("")
                
                secenekler = q.get("secenekler", {})
                for key in ["A", "B", "C", "D", "E"]:
                    st.write(f"**{key})** {secenekler.get(key, '')}")
                
                st.write("")
                with st.popover(f"Soru #{idx} Doğru Cevap ve Çözümü"):
                    st.write(f"**Doğru Cevap:** {q.get('dogru_cevap')}")
                    st.write(f"**Çözüm Açıklaması:** {q.get('cozum_aciklamasi')}")
    else:
        for b_idx, baglam in enumerate(results, 1):
            with st.expander(f"📌 Bağlam Seti #{b_idx} | Zorluk: {baglam.get('zorluk_seviyesi', difficulty_option)}", expanded=True):
                
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
        doc_file = create_word_document(results, active_mode)
        st.download_button(
            label="📄 Soruları Word (.docx) Olarak İndir",
            data=doc_file,
            file_name="osym_tarih_sorulari.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
        
    # JSON İndirme Butonu
    with col_dl2:
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Soruları JSON Olarak İndir",
            data=json_str,
            file_name="osym_tarih_sorulari.json",
            mime="application/json"
        )
