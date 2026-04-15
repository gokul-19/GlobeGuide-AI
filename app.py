import io
import os
import time
from datetime import date

import streamlit as st
from google import genai
from google.genai import types

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

# 1. SETUP CONFIG
st.set_page_config(page_title="GlobeGuide-AI", page_icon="🌍", layout="wide")

# 2. API KEY HANDLER
# It checks Secrets first, then Environment Variables
try:
    api_key_source = st.secrets["api_keys"]["GEMINI_API_KEY"]
except:
    api_key_source = os.environ.get("GEMINI_API_KEY", "")

# 3. PDF GENERATOR
def generate_pdf(dest, text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(name="T", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1A73E8"))
    story.append(Paragraph(f"Itinerary: {dest}", title_style))
    story.append(Spacer(1, 20))
    
    body_style = ParagraphStyle("B", parent=styles["Normal"], fontSize=11, leading=14)
    story.append(Paragraph(text.replace("\n", "<br/>"), body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# 4. SIDEBAR (Check Indentation carefully here!)
with st.sidebar:
    st.title("Settings")
    source = st.text_input("From", "Hyderabad")
    destination = st.text_input("To", "London")
    days = st.slider("Days", 1, 14, 5)
    
    st.divider()
    user_key = st.text_input("Own API Key (Optional)", type="password")
    
    # Defaults to 1.5-flash because it's the MOST reliable for free users
    model_id = st.selectbox("Model", ["gemini-1.5-flash", "gemini-3.1-flash-preview"])
    
    generate_btn = st.button("Generate Plan", use_container_width=True)

# 5. MAIN LOGIC
st.title("🌍 GlobeGuide-AI")

if generate_btn:
    # Use the key from sidebar if provided, otherwise use the system key
    final_key = user_key if user_key else api_key_source
    
    if not final_key:
        st.error("⚠️ No API Key found! Add 'GEMINI_API_KEY' to your Streamlit Secrets.")
    else:
        with st.spinner("Thinking..."):
            try:
                client = genai.Client(api_key=final_key)
                prompt = f"Plan a {days} day trip from {source} to {destination}."
                
                response = client.models.generate_content(model=model_id, contents=prompt)
                
                if response.text:
                    st.success("Success!")
                    st.markdown(response.text)
                    
                    pdf = generate_pdf(destination, response.text)
                    st.download_button("📥 Download PDF", data=pdf, file_name="plan.pdf")
            
            except Exception as e:
                # This catches the 'Quota' and 'Not Found' errors we saw in your screenshots
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.error("⚠️ Quota Exceeded! Wait 1 minute or use a new API key.")
                elif "404" in str(e):
                    st.error("⚠️ Model not found. Please select 'gemini-1.5-flash' in the sidebar.")
                else:
                    st.error(f"⚠️ Error: {str(e)}")
