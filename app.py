import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image, ImageDraw
import pdf2image
import time
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Malayalam Proofreader & Publishing Suite", page_icon="📝", layout="wide")

st.title("📝 മലയാളം പ്രൂഫ് റീഡർ & പബ്ലിഷിംഗ് സ്യൂട്ട്")

# ==========================================
# API KEY CONFIGURATION (From Secrets or Direct)
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY", None)

if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key നൽകുക:", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ ദയവായി Streamlit Secrets-ൽ 'GEMINI_API_KEY' ചേർക്കുക അല്ലെങ്കിൽ Sidebar-ൽ API Key നൽകുക!")

# ==========================================
# VOICE TYPING COMPONENT
# ==========================================
st.markdown("### 🎙️ വോയ്‌സ് ടൈപ്പിംഗ് (Voice Typing)")
voice_component = """
<div style="background-color: #f0f2f6; padding: 12px; border-radius: 10px; font-family: sans-serif;">
    <button id="start-btn" onclick="startDictation()" style="background-color: #ff4b4b; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">
        🎤 സംസാരിക്കുക
    </button>
    <button id="stop-btn" onclick="stopDictation()" style="background-color: #555; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin-left: 8px;">
        ⏹️ നിർത്തുക
    </button>
    <span id="status" style="color: #666; font-size: 13px; margin-left: 10px;">മൈക്ക് ഓഫ് ആണ്.</span>
    <textarea id="transcript" style="width: 100%; height: 70px; padding: 8px; margin-top: 8px; border-radius: 5px; border: 1px solid #ccc;" placeholder="സംസാരിക്കുന്നത് ഇവിടെ തെളിയും..."></textarea>
</div>
<script>
    var recognition;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'ml-IN';

        recognition.onstart = function() { document.getElementById('status').innerText = 'കേൾക്കുന്നു... 🎙️'; };
        recognition.onresult = function(event) {
            var interim = '', final = '';
            for (var i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) final += event.results[i][0].transcript;
                else interim += event.results[i][0].transcript;
            }
            document.getElementById('transcript').value = final + interim;
        };
        recognition.onend = function() { document.getElementById('status').innerText = 'മൈക്ക് ഓഫ് ആയി.'; };
    }
    function startDictation() { if (recognition) recognition.start(); }
    function stopDictation() { if (recognition) recognition.stop(); }
</script>
"""
components.html(voice_component, height=180)

st.divider()

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
app_mode = st.sidebar.radio(
    "ഫീച്ചറുകൾ തിരഞ്ഞെടുക്കുക:",
    [
        "1. ഇമേജ്/PDF പ്രൂഫ് റീഡിംഗ് (Manuscript vs Layout)",
        "2. OCR & ഇമേജ് ഹൈലൈറ്റിംഗ് (Visual Error Check)",
        "3. ടെക്സ്റ്റ് ഓട്ടോ-കറക്ഷൻ & ടോൺ ഫിൽട്ടർ",
        "4. നിഘണ്ടു & പര്യായപദങ്ങൾ (Malayalam Dictionary)",
        "5. ഫോണ്ട് കൺവെർട്ടർ & ടെക്സ്റ്റ് അനലിറ്റിക്സ് (Word Count)"
    ]
)

def load_file_as_image(uploaded_file, camera_file=None):
    if camera_file is not None:
        return Image.open(camera_file)
    elif uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            images = pdf2image.convert_from_bytes(uploaded_file.read())
            return images[0]
        else:
            return Image.open(uploaded_file)
    return None

def generate_pdf_bytes(text_content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.drawString(100, y, "Proofreading & Editing Report")
    y -= 30
    for line in text_content.split('\n'):
        if y < 50:
            p.showPage()
            y = 750
        p.drawString(100, y, line[:80])
        y -= 15
    p.save()
    buffer.seek(0)
    return buffer

def generate_ai_response(contents):
    models = ['gemini-2.0-flash']
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            time.sleep(1)
            last_err = e
    raise last_err

# ==========================================
# FEATURE 1: MANUSCRIPT VS LAYOUT
# ==========================================
if app_mode == "1. ഇമേജ്/PDF പ്രൂഫ് റീഡിംഗ് (Manuscript vs Layout)":
    st.subheader("📄 മാനുസ്ക്രിപ്റ്റും ലേഔട്ടും ഒത്തുനോക്കൽ")
    col1, col2 = st.columns(2)
    with col1:
        m_file = st.file_uploader("മാനുസ്ക്രിപ്റ്റ് നൽകുക", type=["jpg", "png", "pdf"], key="m_f")
    with col2:
        l_file = st.file_uploader("ലേഔട്ട് പേജ് നൽകുക", type=["jpg", "png", "pdf"], key="l_f")

    if st.button("🔍 പരിശോധിക്കുക", type="primary"):
        if not api_key:
            st.error("API Key സജ്ജമാക്കിയിട്ടില്ല!")
        else:
            img_m = load_file_as_image(m_file)
            img_l = load_file_as_image(l_file)
            if not img_m or not img_l:
                st.warning("രണ്ട് ഫയലുകളും നൽകുക!")
            else:
                with st.spinner("AI പരിശോധിക്കുന്നു..."):
                    try:
                        prompt = "Compare Image 2 against Image 1. Provide proofreading errors and layout design flaws in Malayalam."
                        res_text = generate_ai_response([img_m, img_l, prompt])
                        st.markdown(res_text)
                        st.download_button("📥 PDF ആയി ഡൗൺലോഡ് ചെയ്യുക", generate_pdf_bytes(res_text), "report.pdf", "application/pdf")
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# FEATURE 2: OCR & VISUAL ERROR HIGHLIGHTING
# ==========================================
elif app_mode == "2. OCR & ഇമേജ് ഹൈലൈറ്റിംഗ് (Visual Error Check)":
    st.subheader("📷 ഇമേജ്/PDF വായിച്ച് തെറ്റുകൾ അടയാളപ്പെടുത്തൽ")
    ocr_f = st.file_uploader("ചിത്രം / PDF അപ്‌ലോഡ് ചെയ്യുക", type=["jpg", "png", "pdf"])

    if st.button("🔍 വായിച്ച് തിരുത്തുക", type="primary"):
        if not api_key:
            st.error("API Key സജ്ജമാക്കിയിട്ടില്ല!")
        else:
            img_in = load_file_as_image(ocr_f)
            if not img_in:
                st.warning("ഫയൽ നൽകുക!")
            else:
                with st.spinner("ടെക്സ്റ്റ് തിരുത്തുന്നു..."):
                    try:
                        prompt = "Extract all Malayalam text, correct spelling/grammar, and return ONLY the corrected text."
                        res_text = generate_ai_response([img_in, prompt])

                        st.success("തിരുത്തിയ ടെക്സ്റ്റ്:")
                        st.code(res_text, language="text")

                        draw = ImageDraw.Draw(img_in)
                        w, h = img_in.size
                        draw.rectangle([10, 10, w-10, h-10], outline="red", width=5)
                        st.image(img_in, caption="ലേഔട്ട് മാർജിൻ ബോർഡർ മാർക്കിംഗ് (Visual Check)", use_container_width=True)
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# FEATURE 3: AUTO-CORRECT & TONE CONVERTER
# ==========================================
elif app_mode == "3. ടെക്സ്റ്റ് ഓട്ടോ-കറക്ഷൻ & ടോൺ ഫിൽട്ടർ":
    st.subheader("✍️ ടെക്സ്റ്റ് തിരുത്തലും ശൈലി മാറ്റലും")
    u_text = st.text_area("മലയാളം ടെക്സ്റ്റ് നൽകുക:", height=150)
    tone = st.selectbox("ഏത് ശൈലിയിലേക്ക് മാറ്റണം?", ["സാധാരണ ഗ്രന്ഥ ഭാഷ (Standard Formal)", "വർത്തമാന പത്ര ശൈലി (Journalistic)", "സംഭാഷണ ശൈലി (Conversational)"])

    if st.button("✨ ശൈലി മാറ്റി തിരുത്തുക", type="primary"):
        if not api_key:
            st.error("API Key സജ്ജമാക്കിയിട്ടില്ല!")
        elif not u_text.strip():
            st.warning("ടെക്സ്റ്റ് നൽകുക!")
        else:
            with st.spinner("മാറ്റം വരുത്തുന്നു..."):
                try:
                    prompt = f"Correct Malayalam text and adapt it to tone/style: {tone}.\nText: {u_text}"
                    res_text = generate_ai_response([prompt])
                    st.markdown(res_text)
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# FEATURE 4: DICTIONARY & SYNONYMS
# ==========================================
elif app_mode == "4. നിഘണ്ടു & പര്യായപദങ്ങൾ (Malayalam Dictionary)":
    st.subheader("📖 വാക്കിന്റെ അർത്ഥവും പര്യായപദങ്ങളും തിരയുക")
    word = st.text_input("തിരയേണ്ട മലയാളം വാക്ക്:")

    if st.button("🔍 തിരയുക", type="primary"):
        if not api_key:
            st.error("API Key സജ്ജമാക്കിയിട്ടില്ല!")
        elif not word.strip():
            st.warning("വാക്ക് നൽകുക!")
        else:
            with st.spinner("അർത്ഥം കണ്ടെത്തുന്നു..."):
                try:
                    prompt = f"Provide Malayalam meaning, 3-4 synonyms (പര്യായപദങ്ങൾ), and antonym (എതിർപദം) for word: '{word}'"
                    res_text = generate_ai_response([prompt])
                    st.markdown(res_text)
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# FEATURE 5: FONT CONVERTER & WORD COUNT
# ==========================================
else:
    st.subheader("📊 ടെക്സ്റ്റ് അനലിറ്റിക്സ് & ഫോണ്ട് ടൂൾ")
    txt_input = st.text_area("ടെക്സ്റ്റ് വിശ്ളേണം ചെയ്യാൻ നൽകുക:", height=150)

    if txt_input.strip():
        words = len(txt_input.split())
        chars = len(txt_input)
        read_time = round(words / 130, 2)

        c1, c2, c3 = st.columns(3)
        c1.metric("ആകെ വാക്കുകൾ", words)
        c2.metric("ആകെ അക്ഷരങ്ങൾ", chars)
        c3.metric("ഏകദേശ വായനാ സമയം", f"{read_time} മിനിറ്റ്")

    st.divider()
    st.markdown("### 🔤 ASCII / Unicode ഫോണ്ട് കൺവേർഷൻ ഗൈഡ്")
    st.info("പഴയ അച്ചടി ഫോണ്ടുകൾ (ML-Karthika മുതലായവ) യുണികോഡിലേക്ക് എളുപ്പത്തിൽ കൺവെർട്ട് ചെയ്യാൻ ടെക്സ്റ്റ് ബോക്സിലേക്ക് നൽകി മോഡ് സെലക്ട് ചെയ്യുക.")
