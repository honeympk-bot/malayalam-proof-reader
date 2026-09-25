import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Malayalam Proofreader", page_icon="📝")

st.title("📝 മലയാളം പ്രൂഫ് റീഡർ (InDesign Proofreader)")
st.write("മാനുസ്‌ക്രിപ്റ്റും ടൈപ്പ് ചെയ്ത ലേഔട്ടും അപ്‌ലോഡ് ചെയ്ത് തെറ്റുകൾ പരിശോധിക്കുക.")

api_key = st.sidebar.text_input("Gemini API Key നൽകുക:", type="password")

st.subheader("ചിത്രങ്ങൾ അപ്‌ലോഡ് ചെയ്യുക")
col1, col2 = st.columns(2)

with col1:
    manuscript_file = st.file_uploader("മാനുസ്‌ക്രിപ്റ്റ് ചിത്രം (Original)", type=["jpg", "jpeg", "png"])
    if manuscript_file:
        st.image(manuscript_file, caption="Manuscript", use_container_width=True)

with col2:
    layout_file = st.file_uploader("ലേഔട്ട് ചിത്രം (Typeset Layout)", type=["jpg", "jpeg", "png"])
    if layout_file:
        st.image(layout_file, caption="Layout Page", use_container_width=True)

if st.button("🔍 പ്രൂഫ് പരിശോധിക്കുക", type="primary"):
    if not api_key:
        st.error("ദയവായി Sidebar-ൽ Gemini API Key നൽകുക!")
    elif not manuscript_file or not layout_file:
        st.warning("ദയവായി രണ്ട് ചിത്രങ്ങളും അപ്‌ലോഡ് ചെയ്യുക!")
    else:
        with st.spinner("AI പ്രൂഫ് പരിശോധിക്കുന്നു..."):
            try:
                client = genai.Client(api_key=api_key)
                img_manuscript = Image.open(manuscript_file)
                img_layout = Image.open(layout_file)

                prompt = """
                You are an expert Malayalam book editor and proofreader.
                Image 1 is the handwritten or original manuscript.
                Image 2 is the typeset InDesign page layout.

                Compare Image 2 against Image 1 very carefully and list all differences and errors found in Image 2:
                1. Missing words or sentences (വിട്ടുപോയ വാക്കുകൾ/വരികൾ)
                2. Spelling/Typo errors (അക്ഷരത്തെറ്റുകൾ)
                3. Grammar, Sandhi, or Vibhakthi errors (വ്യാകരണ / സന്ധി തെറ്റുകൾ)
                
                Please format your response clearly in Malayalam using bullet points.
                """

                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=[prompt, img_manuscript, img_layout]
                )

                st.success("പരിശോധന പൂർത്തിയായി!")
                st.subheader("📋 പരിശോധനാ ഫലം:")
                st.write(response.text)

            except Exception as e:
                st.error(f"എറർ സംഭവിച്ചു: {e}")
              
