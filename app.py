import io
import os
from datetime import date

import streamlit as st
import google.generativeai as genai

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors


# ------------------------------------
# App Setup
# ------------------------------------
st.set_page_config(page_title="AI Travel Planner", layout="wide")

# Load API Key
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = os.environ.get("GOOGLE_API_KEY", "")


# ------------------------------------
# Styled PDF Generator
# ------------------------------------
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

    for p in itinerary_text.split("\n\n"):
        story.append(Paragraph(p.replace("\n", "<br/>"), body))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ------------------------------------
# UI
# ------------------------------------
st.title("🌍 AI Travel Planner")
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
        [
            "English", "Spanish", "French", "German", "Japanese", "Chinese",
            "Portuguese", "Arabic", "Hindi", "Bengali", "Tamil", "Telugu",
            "Korean", "Italian", "Russian", "Dutch"
        ]
    )

    interests = st.text_input("Interests", "nature, historical sites")
    dietary = st.text_input("Dietary Restrictions", "None")
    activity_level = st.selectbox("Activity Level", ["Low", "Moderate", "High"])
    accommodation_preference = st.selectbox("Accommodation", ["Hotel", "Hostel", "Apartment"])
    travel_style = st.selectbox("Travel Style", ["Relaxed", "Fast-Paced", "Adventurous"])
    landmarks = st.text_input("Must Visit Landmarks", "Eiffel Tower, Grand Canyon")

    st.header("Model Settings")
    model_choice = st.selectbox(
        "Gemini Model",
        [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
    )

    uploaded_image = st.file_uploader("Upload an image (optional)", ["jpg", "png"])

    generate = st.button("Generate Travel Plan")


# ------------------------------------
# Gemini Prompt
# ------------------------------------
def build_prompt():
    return f"""
Create a detailed travel itinerary in {language} for a trip from {source} to {destination} starting on {date_str}.
Trip duration: {duration} days.
Budget: {currency} {budget}.

Interests: {interests}
Dietary restrictions: {dietary}
Activity level: {activity_level}
Accommodation preference: {accommodation_preference}
Travel style: {travel_style}
Must-visit landmarks: {landmarks}

Format:
- Day-by-day itinerary
- Morning, afternoon, evening schedule
- Food recommendations
- Transport tips
- Final: "Travel Checklist"
"""


# ------------------------------------
# Gemini API Call
# ------------------------------------
def call_gemini(prompt, image_bytes=None):
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(model_choice)

    if image_bytes:
        res = model.generate_content([prompt, image_bytes])
    else:
        res = model.generate_content(prompt)

    return res.text


# ------------------------------------
# Run Generator
# ------------------------------------
if generate:
    if not API_KEY:
        st.error("❌ API Key missing. Add it to .streamlit/secrets.toml")
    else:
        st.info("⏳ Generating travel plan...")

        prompt = build_prompt()
        image_bytes = uploaded_image.read() if uploaded_image else None

        itinerary = call_gemini(prompt, image_bytes)

        st.success("✔ Your Travel Itinerary is Ready!")
        st.markdown(itinerary)

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

        st.download_button(
            "📄 Download Styled PDF",
            pdf_buffer,
            "travel_itinerary.pdf",
            "application/pdf"
        )

        st.download_button(
            "📄 Download TXT",
            itinerary,
            "travel_itinerary.txt",
            "text/plain"
        )
