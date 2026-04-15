import io
import os
import time
from datetime import date

import streamlit as st
from google import genai
from google.genai import types

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(page_title="GlobeGuide-AI", page_icon="🌍", layout="wide")

# -----------------------------
# API Key Logic (Uses GEMINI_API_KEY)
# -----------------------------
# On your Mac terminal: export GEMINI_API_KEY='your_key'
# On Streamlit Cloud: Add GEMINI_API_KEY to Secrets
try:
    DEFAULT_API_KEY = st.secrets["api_keys"]["GEMINI_API_KEY"]
except:
    DEFAULT_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# -----------------------------
# PDF Generator
# -----------------------------
def generate_pdf(trip_details: dict, itinerary_text: str):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = ParagraphStyle(name="T", parent=styles["Title"], fontSize=24, textColor=colors.HexColor("#1A73E8"))
    story.append(Paragraph(f"🌍 Trip to {trip_details['destination']}", title))
    story.append(Spacer(1, 20))

    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=11, leading=14)
    clean_text = itinerary_text.replace("\n", "<br/>")
    story.append(Paragraph(clean_text, body))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------
# Sidebar Configuration
# -----------------------------
with st.sidebar:
    st.title("Trip Settings")
    
    source = st.text_input("Source", "Hyderabad")
    destination = st.text_input("Destination", "London")
    duration = st.slider("Duration (Days)", 1, 14, 5)
    
    st.divider()
    
    st.header("API & Model")
    user_key = st.text_input("Custom Gemini Key (Optional)", type="password")
    
    # Updated 2026 Model IDs
    model_id = st.selectbox(
        "Gemini Model", 
        ["gemini-3.1-flash-preview", "gemini-3.1-pro-preview", "gemini-1.5-flash"]
    )
    
    generate_btn = st.button("Generate Travel Plan", use_container_width=True)

# -----------------------------
# Main Content Area
# -----------------------------
st.title("🌍 GlobeGuide-AI")

if generate_btn:
    api_key = user_key if user_key else DEFAULT_API_KEY
    
    if not api_key:
        st.error("⚠️ No API Key found. Please set GEMINI_API_KEY in your secrets or sidebar.")
    else:
        with st.spinner(f"Gemini {model_id} is thinking..."):
            client = genai.Client(api_key=api_key)
            
            prompt = f"Create a detailed {duration}-day travel itinerary from {source} to {destination}. Include food spots and transport."

            try:
                # Using Gemini 3 SDK generate_content
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                
                result_text = response.text
                st.success("Plan Generated!")
                st.markdown(result_text)
                
                # PDF Download
                pdf_data = generate_pdf({"destination": destination}, result_text)
                st.download_button("📥 Download PDF", data=pdf_data, file_name="itinerary.pdf")
                
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ Quota Exceeded! Please wait 60 seconds or switch to 'gemini-1.5-flash'.")
                elif "404" in str(e):
                    st.error(f"⚠️ Model '{model_id}' not found. Try 'gemini-1.5-flash'.")
                else:
                    st.error(f"⚠️ Error: {str(e)}")
