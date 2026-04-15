import io
import os
import time
from datetime import date

import streamlit as st
from google import genai
from google.genai.types import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors

# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(page_title="GlobeGuide-AI", page_icon="🌍", layout="wide")

# -----------------------------
# API Key Logic
# -----------------------------
try:
    DEFAULT_API_KEY = st.secrets["api_keys"]["GOOGLE_API_KEY"]
except:
    DEFAULT_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# -----------------------------
# PDF Generator
# -----------------------------
def generate_styled_pdf_buffer(trip_details: dict, itinerary_text: str):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Title"],
        fontSize=26,
        leading=30,
        alignment=1,
        textColor=colors.HexColor("#1A73E8")
    )

    story.append(Spacer(1, 20))
    story.append(Paragraph("✈️ AI Travel Itinerary", title_style))
    story.append(Spacer(1, 15))

    sub = ParagraphStyle(name="Sub", parent=styles["Normal"], fontSize=12, alignment=1)
    story.append(Paragraph(f"{trip_details['source']} to {trip_details['destination']}", sub))
    story.append(Paragraph(f"Start: {trip_details['date']} | {trip_details['duration']} Days", sub))
    story.append(Spacer(1, 30))

    summary_data = [
        ["Field", "Details"],
        ["Budget", f"{trip_details['currency']} {trip_details['budget']}"],
        ["Style", trip_details["travel_style"]],
        ["Accommodation", trip_details["accommodation_preference"]],
        ["Language", trip_details["language"]]
    ]

    table = Table(summary_data, colWidths=[120, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A73E8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("<b>Detailed Itinerary</b>", styles["Heading2"]))
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    
    # Clean up text for PDF
    clean_text = itinerary_text.replace("\n", "<br/>")
    story.append(Paragraph(clean_text, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("Trip Configuration")
    
    source = st.text_input("Source", "New York")
    destination = st.text_input("Destination", "Paris")
    date_input = st.date_input("Start Date", date.today())
    duration = st.slider("Duration (days)", 1, 30, 5)
    
    st.divider()
    
    budget = st.number_input("Budget", min_value=100, value=1500)
    currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP"])
    
    st.header("Preferences")
    language = st.selectbox("Itinerary Language", ["English", "Hindi", "French", "Spanish"])
    travel_style = st.selectbox("Travel Style", ["Relaxed", "Fast-Paced", "Adventurous"])
    accommodation_preference = st.selectbox("Accommodation", ["Hotel", "Hostel", "Airbnb"])
    
    st.header("API & Model")
    user_api_key = st.text_input("Custom API Key (Optional)", type="password")
    
    # CORRECTED MODELS
    model_choice = st.selectbox(
        "Gemini Model",
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    )
    
    uploaded_image = st.file_uploader("Upload reference image", type=["jpg", "png"])
    generate_btn = st.button("Generate Plan", use_container_width=True)

# -----------------------------
# API Logic
# -----------------------------
def call_gemini(api_key, model, prompt, image_bytes):
    key = api_key if api_key else DEFAULT_API_KEY
    if not key:
        return "ERROR: Missing API Key."

    client = genai.Client(api_key=key)
    content_list = [prompt]
    
    if image_bytes:
        content_list.append(Image(content=image_bytes, mime_type="image/jpeg"))

    # Retry loop for Quota Exceeded
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model, contents=content_list)
            return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < 2:
                    time.sleep(5)
                    continue
            return f"⚠️ API Error: {str(e)}"

# -----------------------------
# Main UI
# -----------------------------
st.title("🌍 GlobeGuide-AI")

if generate_btn:
    with st.spinner("Artificial Intelligence is crafting your journey..."):
        prompt = f"""
        Create a {duration}-day travel itinerary from {source} to {destination}.
        Start Date: {date_input.strftime('%Y-%m-%d')}
        Budget: {currency} {budget}
        Language: {language}
        Style: {travel_style}
        Accommodation: {accommodation_preference}
        Include daily schedules, food spots, and travel tips.
        """
        
        img_data = uploaded_image.read() if uploaded_image else None
        result = call_gemini(user_api_key, model_choice, prompt, img_data)
        
        if "⚠️" in result or "ERROR" in result:
            st.error(result)
        else:
            st.success("Plan Generated!")
            st.markdown(result)
            
            # PDF Generation
            pdf = generate_styled_pdf_buffer({
                "source": source, "destination": destination, "date": date_input,
                "duration": duration, "budget": budget, "currency": currency,
                "language": language, "travel_style": travel_style,
                "accommodation_preference": accommodation_preference
            }, result)
            
            st.download_button("📥 Download PDF Itinerary", data=pdf, file_name="trip_plan.pdf")
