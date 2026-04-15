import io
import os
import time
from datetime import date

import streamlit as st
from google import genai
from google.genai.types import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(page_title="GlobeGuide-AI", page_icon="🌍", layout="wide")

# -----------------------------
# API Key Logic
# -----------------------------
try:
    # This pulls the key from your Streamlit Cloud Secrets
    DEFAULT_API_KEY = st.secrets["api_keys"]["GOOGLE_API_KEY"]
except:
    # This pulls from your local environment if running on your MacBook
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
    
    # Simple conversion for PDF display
    clean_text = itinerary_text.replace("\n", "<br/>")
    story.append(Paragraph(clean_text, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------
# Sidebar Configuration
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
    user_api_key = st.text_input("Custom API Key (Optional)", type="password", help="Overrides default key")
    
    # STABLE MODELS ONLY (Removed -exp to avoid 404 errors)
    model_choice = st.selectbox(
        "Gemini Model",
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
    )
    
    uploaded_image = st.file_uploader("Upload reference image (optional)", type=["jpg", "png"])
    generate_btn = st.button("Generate Plan", use_container_width=True)

# -----------------------------
# Gemini API Execution
# -----------------------------
def call_gemini(api_key, model, prompt, image_bytes):
    # Determine which key to use
    key = api_key if api_key else DEFAULT_API_KEY
    if not key:
        return "ERROR: Missing API Key. Check sidebar or secrets."

    client = genai.Client(api_key=key)
    content_list = [prompt]
    
    if image_bytes:
        content_list.append(Image(content=image_bytes, mime_type="image/jpeg"))

    # Retry mechanism for Quota (RESOURCE_EXHAUSTED) errors
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model, contents=content_list)
            return response.text
        except Exception as e:
            # If hit by rate limits, wait 10 seconds and try again
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < 2:
                    time.sleep(10)
                    continue
            return f"⚠️ API Error: {str(e)}"

# -----------------------------
# Main Content Area
# -----------------------------
st.title("🌍 GlobeGuide-AI")
st.subheader("Your AI-Powered Travel Planner")

if generate_btn:
    with st.spinner("Our AI is scouting the best routes for you..."):
        # Format the prompt
        prompt = f"""
        Generate a comprehensive {duration}-day travel itinerary from {source} to {destination}.
        Trip starts on: {date_input.strftime('%Y-%m-%d')}
        Budget: {currency} {budget}
        Output Language: {language}
        Style: {travel_style}
        Accommodation: {accommodation_preference}
        
        Please include:
        1. A daily schedule (Morning, Afternoon, Evening).
        2. Top food and cafe recommendations.
        3. Local transport tips.
        4. A short travel checklist.
        """
        
        # Read image if provided
        img_data = uploaded_image.read() if uploaded_image else None
        
        # Make the API call
        result = call_gemini(user_api_key, model_choice, prompt, img_data)
        
        # Display the output
        if "⚠️" in result or "ERROR" in result:
            st.error(result)
        else:
            st.success("Itinerary successfully generated!")
            st.markdown(result)
            
            # Create the PDF file for download
            pdf = generate_styled_pdf_buffer({
                "source": source, "destination": destination, "date": date_input,
                "duration": duration, "budget": budget, "currency": currency,
                "language": language, "travel_style": travel_style,
                "accommodation_preference": accommodation_preference
            }, result)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download PDF Itinerary", data=pdf, file_name=f"Travel_Plan_{destination}.pdf")
            with col2:
                st.download_button("📝 Download as Text", data=result, file_name=f"Travel_Plan_{destination}.txt")
