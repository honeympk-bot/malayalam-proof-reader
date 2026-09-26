import streamlit as st
from google import genai
from PIL import Image
import pdf2image
import time

st.set_page_config(page_title="Malayalam Proofreader & Layout Editor", page_icon="📝")

st.title("📝 മലയാളം പ്രൂഫ് റീഡർ & ലേഔട്ട് എഡിറ്റർ")
st.write("മാനുസ്ക്രിപ്റ്റും ലേഔട്ടും അപ്‌ലോഡ് ചെയ്ത് തെറ്റുകളും ലേഔട്ട് പോരായ്മകളും പരിശോധിക്കുക.")

# നിങ്ങളുടെ API Key
api_key = "AQ.Ab8RN6JuNvwjcA6U90BwPmzIHkBhuCrK7j_vwZUz94zKIfNo2A"

def load_file_as_image(uploaded_file, camera_file=None):
    """ഫയൽ (PDF/Image) അല്ലെങ്കിൽ ക്യാമറ ഫോട്ടോ ലഭ്യമാക്കുന്നു."""
    if camera_file is not None:
        return Image.open(camera_file)
    elif uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            images = pdf2image.convert_from_bytes(uploaded_file.read())
            return images[0]
        else:
            return Image.open(uploaded_file)
    return None

st.subheader("1. ചിത്രങ്ങൾ / ഫയലുകൾ ലഭ്യമാക്കുക")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**മാനുസ്ക്രിപ്റ്റ് (Original)**")
    m_input_type = st.radio("അപ്‌ലോഡ് രീതി (Manuscript):", ["ഫയൽ (JPG/PNG/PDF)", "ക്യാമറ ഫോട്ടോ"], key="m_type")
    manuscript_file = None
    manuscript_cam = None
    if m_input_type == "ഫയൽ (JPG/PNG/PDF)":
        manuscript_file = st.file_uploader("മാനുസ്ക്രിപ്റ്റ് ഫയൽ നൽകുക", type=["jpg", "jpeg", "png", "pdf"], key="m_file")
    else:
        manuscript_cam = st.camera_input("ക്യാമറ ഉപയോഗിച്ച് ഫോട്ടോ എടുക്കുക", key="m_cam")

with col2:
    st.markdown("**ലേഔട്ട് പേജ് (Typeset Layout)**")
    l_input_type = st.radio("അപ്‌ലോഡ് രീതി (Layout):", ["ഫയൽ (JPG/PNG/PDF)", "ക്യാമറ ഫോട്ടോ"], key="l_type")
    layout_file = None
    layout_cam = None
    if l_input_type == "ഫയൽ (JPG/PNG/PDF)":
        layout_file = st.file_uploader("ലേഔട്ട് ഫയൽ നൽകുക", type=["jpg", "jpeg", "png", "pdf"], key="l_file")
    else:
        layout_cam = st.camera_input("ക്യാമറ ഉപയോഗിച്ച് ഫോട്ടോ എടുക്കുക", key="l_cam")

st.subheader("2. പരിശോധനാ ഓപ്ഷനുകൾ (Filters)")
check_option = st.radio(
    "എന്തൊക്കെ കാര്യങ്ങളാണ് പരിശോധിക്കേണ്ടത്?",
    ["എല്ലാ കാര്യങ്ങളും (പ്രൂഫ് + ലേഔട്ട് പോരായ്മകൾ)", "അക്ഷരത്തെറ്റുകളും വിട്ടുപോയ വാക്കുകളും മാത്രം", "ലേഔട്ട് & ഡിസൈൻ പോരായ്മകൾ മാത്രം"]
)

if st.button("🔍 പരിശോധന ആരംഭിക്കുക", type="primary"):
    img_manuscript = load_file_as_image(manuscript_file, manuscript_cam)
    img_layout = load_file_as_image(layout_file, layout_cam)

    if not api_key:
        st.error("API Key കണ്ടെത്താൻ സാധിച്ചില്ല!")
    elif img_manuscript is None or img_layout is None:
        st.warning("രണ്ട് വശത്തേക്കുമുള്ള ഫയലുകൾ അല്ലെങ്കിൽ ചിത്രങ്ങൾ നൽകുക!")
    else:
        with st.spinner("AI പരിശോധിക്കുന്നു... ദയവായി കാത്തിരിക്കുക..."):
            try:
                client = genai.Client(api_key=api_key)

                # ഫിൽട്ടറുകൾക്കനുസരിച്ചുള്ള പ്രോംപ്റ്റ് തയ്യാറാക്കുന്നു
                prompt_details = ""
                if check_option == "അക്ഷരത്തെറ്റുകളും വിട്ടുപോയ വാക്കുകളും മാത്രം":
                    prompt_details = """
                    Only check for textual and content errors in Image 2 comparing with Image 1:
                    1. വിട്ടുപോയ വാക്കുകൾ/വരികൾ (Missing words/sentences)
                    2. അക്ഷരത്തെറ്റുകൾ (Spelling/Typo errors)
                    3. വ്യാകരണ / സന്ധി തെറ്റുകൾ (Grammar, Sandhi, or Visargam errors)
                    """
                elif check_option == "ലേഔട്ട് & ഡിസൈൻ പോരായ്മകൾ മാത്രം":
                    prompt_details = """
                    Only analyze Image 2 for book page design and InDesign formatting flaws:
                    1. മാർജിൻ / അലൈൻമെന്റ് പോരായ്മകൾ (Margin, Justification, Alignment)
                    2. ഫോണ്ട് വലുപ്പം / ലൈൻ സ്പേസിങ് പ്രശ്നങ്ങൾ (Font size, Leading/Line spacing, Line overlapping)
                    3. പാരഗ്രാഫ് സ്പേസിങ് & ഇൻഡെന്റേഷൻ (Paragraph indent, Spacing, Widows/Orphans)
                    4. അക്ഷരക്കൂട്ട് / ചിഹ്നങ്ങളുടെ ക്രമീകരണം (Malayalam font rendering/conjunct issues)
                    5. മൊത്തത്തിലുള്ള പേജ് സൗന്ദര്യം (Overall visual balance & suggestions)
                    """
                else:
                    prompt_details = """
                    Perform a complete two-part review in Malayalam:
                    ### PART 1: പ്രൂഫ് പരിശോധന (Text & Content Errors)
                    1. വിട്ടുപോയ വാക്കുകൾ/വരികൾ (Missing words/sentences)
                    2. അക്ഷരത്തെറ്റുകൾ (Spelling/Typo errors)
                    3. വ്യാകരണ / സന്ധി തെറ്റുകൾ (Grammar, Sandhi, or Visargam errors)

                    ### PART 2: ലേഔട്ട് പോരായ്മകൾ (Design & Formatting Flaws)
                    1. മാർജിൻ / അലൈൻമെന്റ് പോരായ്മകൾ (Margin, Alignment)
                    2. ഫോണ്ട് വലുപ്പം / ലൈൻ സ്പേസിങ് പ്രശ്നങ്ങൾ (Font size, Leading)
                    3. പാരഗ്രാഫ് സ്പേസിങ് & ഇൻഡെന്റേഷൻ (Paragraph indent, Widows/Orphans)
                    4. അക്ഷരക്കൂട്ട് / ചിഹ്നങ്ങൾ (Malayalam font rendering issues)
                    5. മൊത്തത്തിലുള്ള പേജ് സൗന്ദര്യം (Visual balance)
                    """

                prompt = f"""
                You are an expert Malayalam book editor and InDesign page layout designer.
                Image 1 is the handwritten or original manuscript.
                Image 2 is the typeset layout.

                {prompt_details}

                Please output the analysis clearly in Malayalam using markdown format.
                """

                models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash']
                response = None
                last_error = None

                for model_name in models_to_try:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[img_manuscript, img_layout, prompt]
                        )
                        if response and response.text:
                            break
                    except Exception as e:
                        last_error = e
                        time.sleep(1)

                if response and response.text:
                    st.success("പരിശോധന പൂർത്തിയായി!")
                    st.markdown(response.text)

                    # റിസൾട്ട് Text/Report ആയി ഡൗൺലോഡ് ചെയ്യാനുള്ള ഫീച്ചർ
                    st.subheader("📥 ഫലം ഡൗൺലോഡ് ചെയ്യുക")
                    st.download_button(
                        label="📄 റിസൾട്ട് Text File ആയി ഡൗൺലോഡ് ചെയ്യുക",
                        data=response.text,
                        file_name="proofreading_report.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"എറർ സംഭവിച്ചു: {last_error}")

            except Exception as e:
                st.error(f"എറർ സംഭവിച്ചു: {e}")
