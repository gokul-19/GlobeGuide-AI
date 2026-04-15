import io
import os
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
# Default API Key (from secrets or env)
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
        fontSize=28,
        leading=32,
        alignment=1,
        textColor=colors.HexColor("#1A73E8")
    )

    story.append(Spacer(1, 40))
    story.append(Paragraph("✈️ AI Travel Itinerary", title_style))
    story.append(Spacer(1, 15))

    sub = ParagraphStyle(
        name="Sub",
        parent=styles["Normal"],
        fontSize=14,
        leading=20,
        alignment=1
    )

    story.append(Paragraph(f"{trip_details['source']} → {trip_details['destination']}", sub))
    story.append(Paragraph(f"Start: {trip_details['date']}", sub))
    story.append(Paragraph(f"Duration: {trip_details['duration']} days", sub))
    story.append(Paragraph(f"Budget: {trip_details['currency']} {trip_details['budget']}", sub))
    story.append(Spacer(1, 40))

    story.append(PageBreak())

    summary = [
        ["Source", trip_details["source"]],
        ["Destination", trip_details["destination"]],
        ["Start Date", trip_details["date"]],
        ["Duration", f"{trip_details['duration']} days"],
        ["Budget", f"{trip_details['currency']} {trip_details['budget']}"],
        ["Language", trip_details["language"]],
        ["Accommodation", trip_details["accommodation_preference"]],
        ["Travel Style", trip_details["travel_style"]],
    ]

    table = Table(summary, colWidths=[140, 320])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#1A73E8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F0F4FF")),
        ("GRID", (0, 0), (-1, -1), 0.8, colors.grey),
        ("BOX", (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("<b>Trip Summary</b>", styles["Heading2"]))
    story.append(table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>Detailed Itinerary</b>", styles["Heading2"]))
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=12, leading=16)

    # Convert Markdown-like line breaks to PDF-friendly breaks
    formatted_itinerary = itinerary_text.replace("\n", "<br/>")
    story.append(Paragraph(formatted_itinerary, body))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------
# Sidebar / Inputs
# -----------------------------
st.title("🌍 GlobeGuide-AI")
st.subheader("Generate your perfect travel itinerary with AI ✨")

with st.sidebar:
    st.header("Trip Details")
    source = st.text_input("Source", "New York")
    destination = st.text_input("Destination", "Los Angeles")
    date_input = st.date_input("Start Date", date.today())
    date_str = date_input.strftime("%Y-%m-%d")
    budget = st.number_input("Budget", min_value=100, value=1000)
    duration = st.slider("Duration (days)", 1, 60, 7)
    currency = st.selectbox("Currency", ["USD", "EUR", "INR", "GBP", "AUD", "JPY"])

    st.header("Preferences")
    language = st.selectbox(
        "Language",
        ["English", "Spanish", "French", "German", "Japanese", "Chinese",
         "Portuguese", "Arabic", "Hindi", "Bengali", "Tamil", "Telugu", "Kannada",
         "Korean", "Italian", "Russian", "Dutch"]
    )
    interests = st.text_input("Interests", "nature, historical sites")
    dietary = st.text_input("Dietary Restrictions", "None")
    activity_level = st.selectbox("Activity Level", ["Low", "Moderate", "High"])
    accommodation_preference = st.selectbox("Accommodation", ["Hotel", "Hostel", "Apartment"])
    travel_style = st.selectbox("Travel Style", ["Relaxed", "Fast-Paced", "Adventurous"])
    landmarks = st.text_input("Must Visit Landmarks", "Eiffel Tower, Grand Canyon")

    st.header("API Key Settings")
    user_api_key = st.text_input(
        "Enter your own API key (optional)",
        value="",
        type="password",
        help="If you provide a key, it will override the default key."
    )

   st.header("Model Settings")
model_choice = st.selectbox(
    "Gemini Model",
    ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
    index=0  # This makes 'flash' the default
)

    uploaded_image = st.file_uploader("Upload an image (optional)", ["jpg", "png"])
    generate = st.button("Generate Travel Plan")

# -----------------------------
# Build Prompt
# -----------------------------
def build_prompt():
    return f"""
Create a detailed travel itinerary in {language} for a trip from {source} to {destination} starting on {date_str}.
Duration: {duration} days.
Budget: {currency} {budget}.

Interests: {interests}
Dietary restrictions: {dietary}
Activity level: {activity_level}
Accommodation preference: {accommodation_preference}
Travel style: {travel_style}
Must visit landmarks: {landmarks}

Provide:
- Full daily plan
- Morning / Afternoon / Evening schedule
- Food recommendations
- Transportation guidance
- Travel checklist
"""

# -----------------------------
# Call Gemini API
# -----------------------------
def call_gemini(prompt, image_bytes=None, api_key=None):
    key_to_use = api_key.strip() if api_key and api_key.strip() else DEFAULT_API_KEY
    if not key_to_use:
        return "⚠️ No API key found! Please enter one in the sidebar or check your secrets.toml."

    client = genai.Client(api_key=key_to_use)

    # Prepare content parts
    contents = [prompt]

    if image_bytes:
        # Handling for newer google-genai SDK
        img = Image(content=image_bytes, mime_type="image/jpeg")
        contents.append(img)

    try:
        result = client.models.generate_content(
            model=model_choice,
            contents=contents
        )
        return result.text
    except Exception as e:
        if "404" in str(e):
            return f"⚠️ Error 404: The model '{model_choice}' was not found. Please try 'gemini-1.5-flash'."
        elif "RESOURCE_EXHAUSTED" in str(e):
            return "⚠️ Gemini API quota exceeded. Please try again later."
        else:
            return f"⚠️ Gemini API error: {e}"

# -----------------------------
# Main Logic
# -----------------------------
if generate:
    with st.spinner("🌍 Planning your journey..."):
        prompt = build_prompt()
        image_bytes = uploaded_image.read() if uploaded_image else None
        itinerary = call_gemini(prompt, image_bytes, api_key=user_api_key)

    if "⚠️" in itinerary:
        st.error(itinerary)
    else:
        st.success("✔ Your Travel Itinerary is Ready!")
        st.markdown(itinerary)

        # Generate PDF
        pdf_buffer = generate_styled_pdf_buffer(
            {
                "source": source,
                "destination": destination,
                "date": date_str,
                "budget": budget,
                "duration": duration,
                "currency": currency,
                "language": language,
                "accommodation_preference": accommodation_preference,
                "travel_style": travel_style,
            },
            itinerary
        )

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📄 Download Styled PDF",
                data=pdf_buffer,
                file_name=f"Travel_Itinerary_{destination}.pdf",
                mime="application/pdf"
            )
        with col2:
            st.download_button(
                "📄 Download TXT File",
                data=itinerary,
                file_name=f"Travel_Itinerary_{destination}.txt",
                mime="text/plain"
            )
