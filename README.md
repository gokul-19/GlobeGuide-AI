# 🌍 GlobeGuide-AI — Smart Travel Planning Assistant  

An AI-powered travel planning assistant to help you find the best travel options across India and the world.

---

## 🌟 Overview
**GlobeGuide-AI** is an intelligent travel planner built using:

- **Streamlit** – for a fast and interactive UI  
- **LangChain** – for managing LLM logic and prompts  
- **Google Generative AI** – for smart, contextual travel recommendations  
- **Live Travel APIs** – (Google Maps, Skyscanner, IRCTC, etc.) for real-time travel data  

It helps users discover optimal travel routes, recommended modes of transport, and AI-generated insights.

---
## 🧠 GlobeGuide-AI — Agentic Architecture Diagram

```
                     ┌────────────────────────────────────┐
                     │           User Interface            │
                     │  (Streamlit Web App / Colab App)   │
                     └───────────────┬────────────────────┘
                                     │ Inputs
                                     ▼
         ┌────────────────────────────────────────────────────────┐
         │              Agent Orchestration Layer (AOL)            │
         │  Controls agent order, error handling, memory passing   │
         └───────────────┬────────────────────────────────────────┘
                         │ Delegates Tasks
     ┌───────────────────┼─────────────────────┬──────────────────────┬───────────────────────┐
     ▼                   ▼                     ▼                      ▼
┌─────────────┐   ┌──────────────┐      ┌───────────────┐       ┌────────────────┐
│ Planner      │   │ Transport    │      │ Budget Agent   │       │ Activity Agent │
│ Agent (A1)   │   │ Agent (A2)   │      │ (A3)           │       │ (A4)           │
│ - Creates    │   │ - Finds best │      │ - Validates     │       │ - Selects best │
│   skeleton   │   │   routes     │      │   full cost     │       │   attractions  │
│   itinerary  │   │ - ETA, modes │      │ - Suggests      │       │ - Day timing   │
│ - Day splits │   │ - Multi-city │      │   cheaper opts  │       │   distribution │
└──────┬──────┘   │              └──────┬───────────────┘       └──────────┬─────┘
       │          │                     │                                  │
       ▼          ▼                     ▼                                  ▼
       ┌────────────────────────────────────────────────────────────────────────┐
       │                       Shared Memory / Context                          │
       │   (All agents write intermediate reasoning + validated results here)   │
       └───────────────┬────────────────────────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  Safety & Consistency    │
            │        Agent (A5)        │
            │ - Removes conflicts      │
            │ - Validates timing       │
            │ - Ensures feasibility    │
            └──────────────┬───────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │ Output Formatter (A6)   │
              │ - Converts agent data   │
              │   into clean itinerary  │
              │ - Adds Travel Checklist │
              │ - Sends for PDF export  │
              └──────────────┬──────────┘
                             │
                             ▼
                ┌──────────────────────────────┐
                │     Final Itinerary Output    │
                │  - Text on screen             │
                │  - Styled PDF                 │
                │  - TXT download               │
                └──────────────────────────────┘
```
---

## ✨ Features

- 🖥️ **User-friendly Travel Interface**  
- 🤖 **AI-powered travel recommendations**  
- 🗺️ **Supports both India and global travel**  
- 🚆 **Real-time travel data** (flights, trains, buses)  
- 🔍 **Search by source and destination**  
- 🧠 **Smart system prompt for accurate results**

---


## 📦 Prerequisites
You will need:

- **Python 3.7+**
- **Google Generative AI API Key**
- Optional API Keys:
  - Google Maps
  - IRCTC travel APIs
  - Skyscanner / flight data APIs

---

## 🔧 Installation

### 1️⃣ Clone the Repository
git clone <repository-url>
cd <repository-directory>

### 2️⃣ Install Required Packages
pip install streamlit langchain google-generativeai

Add additional APIs based on your project setup.

---

## ▶️ Usage

Start the Streamlit application:
streamlit run app.py

Inside the App:

- Enter Source and Destination  
- Click Find Travel Options  
- Receive AI-generated:
  - Travel modes  
  - Route suggestions  
  - Timing & duration  
  - Travel tips  

---

## 🧠 System Prompt
GlobeGuide-AI includes a powerful system prompt designed to:

- Act as a smart global travel assistant  
- Provide India-specific + global travel suggestions  
- Utilize real-time API data  
- Adapt to user preferences  

---

## 🤝 Contributing
Contributions are welcome! Fork the repository and submit PRs for:

- New features  
- UI improvements  
- Bug fixes  

---

## 📜 License
This project is licensed under the MIT License.
Check the LICENSE file for more details.

---

## 📬 Contact
Gokul  
📧 Email: gorthigokul77@gmail.com
