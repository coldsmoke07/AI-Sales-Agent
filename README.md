# WaveNxD AI Sales Representative (SalesGPT Engine)

An AI sales representative built for **WaveNxD Technologies Pvt. Ltd., Kolhapur, Maharashtra** to consult prospective engineering clients on precision no-pressure ultrasonic spray nozzle systems.

Adapted from the stage-aware **SalesGPT** architecture, streamlined into a clean, modular structure with zero bloat.

---

## 1. Feature Completeness (All 7 Required Features + Bonus)

| # | Evaluation Feature | What Was Built & Verified | Status |
|---|---|---|:---:|
| **1** | **Chat & Voice Assistant** | Multi-turn conversational sales persona (*Arjun Kulkarni*). Works via web chat, terminal CLI (`run.py`), Web Speech API microphone STT input, and audio TTS voice output. | **Complete** |
| **2** | **Self-Introduction** | Formally greets prospective clients, identifies company and location (*WaveNxD Technologies Pvt. Ltd., Kolhapur*), and pitches ultrasonic spray nozzle capabilities (soft, low-velocity, fine droplets, no hydraulic pressure). | **Complete** |
| **3** | **Multilingual Replies** | Defaults to English; automatically switches to **Marathi**, **Hindi**, or **Tamil** upon regional input or selection. Preserves metric units (`cP`, `µm`, `kHz`, `ml/min`) naturally. | **Complete** |
| **4** | **Strict Product Knowledge** | Grounded strictly in `catalog.json` (Single Source of Truth). Correctly handles the 180 kHz row (mislabeled as 60 kHz in raw catalog tables). Never invents specs, prices, or lead times; escalates unlisted items with *"I will confirm this with the WaveNxD engineering team."* | **Complete** |
| **5** | **Requirement Discovery** | Dynamically tracks and extracts: Target Industry, Specific Application, Coating Liquid/Material, Liquid Viscosity (cP), Required Feed Rate (ml/min or µl), and Droplet Size (µm). | **Complete** |
| **6** | **Product Recommendation** | Matches discovered parameters to the optimal WaveNxD nozzle family or complete system (e.g. 180 kHz Torch + Micro Fluid Dispensing for stents, High Viscosity Conical for fuel cells, High Flow for industrial spray drying) and provides plain-language technical justification. | **Complete** |
| **7** | **Quotation & Follow-Up** | Collects client Name, Company, Email, Phone Number, and Preferred Callback slot; generates a structured confirmation summary. | **Complete** |
| **★** | **Bonus Features (+5 Marks)** | **Real Email Dispatch** (`smtplib` SMTP/Gmail integration), **Calendar Booking** (RFC-5545 `.ics` file generation & download + Calendly support), **Voice STT/TTS**, and **Clean ChatGPT-style UI**. | **Complete** |

---

## 2. Clean Project Structure

The project has been cleaned and organized into a minimal 4-folder structure without unnecessary bloat:

```text
SalesGPT-main/
├── app.py                      # Main entrypoint: Web server & REST API (/api/chat, /api/catalog, etc.)
├── run.py                      # Interactive terminal CLI runner
├── catalog.json                # Single Source of Truth WaveNxD product catalog
├── requirements.txt            # Minimal dependencies (runs on pure Python standard library)
├── .env.example                # Environment variables template (optional API keys / SMTP)
├── README.md                   # Complete documentation & run guide
├── PRESENTATION_GUIDE.md       # 15-Mark presentation guide & evaluator Q&A notes
│
├── salesgpt/                   # Core Stage-Aware Sales Engine
│   ├── __init__.py             # Module exports
│   ├── agent.py                # SalesAgent controller with dual engine (Deterministic + optional LLM)
│   ├── stages.py               # 7-stage sales pipeline matching evaluation sequence
│   ├── catalog.py              # Catalog knowledge base & recommendation matcher
│   ├── tools.py                # Sales tools: Catalog lookup, Email sender, Calendar invite (.ics)
│   └── multilingual.py         # Multi-language detection & translation (English, Marathi, Hindi, Tamil)
│
├── templates/
│   └── index.html              # Clean ChatGPT-style interface with progress sidebar & catalog modal
│
├── static/
│   ├── style.css               # Clean dark-neutral engineering styling
│   └── script.js               # Frontend chat logic, Web Speech API (STT & TTS), requirement tracking
│
└── sample_outputs/
    └── demo_transcripts.md     # Transcripts for Medical Stent and Fuel Cell scenarios
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.9 or higher (Tested and verified on Python 3.14 on Windows).
- Zero external package installation required for core execution!

### Option A: Launch Web Application (Recommended for Demo)
```bash
python app.py
```
Open your browser at:
```text
http://localhost:5000
```
- Type questions or click suggested response chips.
- Click **"Speak"** for microphone speech-to-text input (Web Speech API).
- Toggle **"Voice Output"** to hear spoken responses from the sales representative.
- Watch the **Requirement Progress** sidebar update dynamically after each turn.
- Click **"WaveNxD Product Catalog"** in the sidebar to inspect official specifications.

### Option B: Interactive Terminal CLI
```bash
python run.py
```
Run a natural multi-turn sales consultation directly from your terminal.

---

## 4. Optional Configurations (Bonus Features)

The application includes a **Built-in Deterministic WaveNxD Consultative Engine** that runs out-of-the-box with **zero API keys required**, guaranteeing 100% catalog compliance and zero demo crashes.

To optionally connect a live LLM or configure real email sending:
```bash
cp .env.example .env
```
On Windows, copy `.env.example` to `.env` using File Explorer or PowerShell. Edit `.env` to configure:
- **LLM Providers**: `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `GROQ_API_KEY`
- **Enquiry Notifications**: Set `GMAIL_MAIL` to the sending Gmail address and `GMAIL_APP_PASSWORD` to its Google App Password. Completed quotation requests, contact details, and the conversation are sent to `ENQUIRY_RECIPIENT_EMAIL` (defaults to `shantanuj0510@gmail.com`) through the configured SMTP server. The form only confirms submission after the email is successfully sent.
- **SMTP Settings**: `SMTP_HOST` and `SMTP_PORT` (defaults: `smtp.gmail.com` and `587`)
- **Calendly Booking**: `CALENDLY_API_KEY`, `CALENDLY_EVENT_UUID`

The `.env` file is git-ignored. Do not commit mailbox passwords or API keys. Until valid sender credentials are configured, the form displays an email configuration error instead of reporting a false success.

---

## 5. Demonstration Walkthrough (Two Required Evaluation Scenarios)

### Scenario 1: Medical Device Client (Stent Coating - English)
1. Assistant greets as Arjun Kulkarni from WaveNxD Technologies, Kolhapur, and pitches ultrasonic nozzles.
2. Select or type: `"We are manufacturing coronary drug-eluting stents and need uniform coating."`
3. Assistant requests material, viscosity, and flow rate.
4. Input: `"Material is PLGA with sirolimus, viscosity is 10 cP, flow rate 5 ml/min, target droplet size 10 µm."`
5. Assistant recommends **Standard Torch at 180 kHz** (10 µm ultra-fine mist, <50 cP) paired with the **Micro Fluid Dispensing System (0 to 200 µl metered dispensing)**.
6. Submit sample contact details: Dr. Amit Patil, StentTech Labs, `amit@stenttech.in`, `+91 9822012345`, Tomorrow 11:00 AM.
7. Assistant emails the enquiry and conversation details to `ENQUIRY_RECIPIENT_EMAIL` and outputs a structured confirmation summary. The WaveNxD team can then send the formal quotation and confirm the callback.

### Scenario 2: Energy Sector Client (Fuel Cell Slurry - Marathi / Hindi Switch)
1. Switch language via top dropdown or type in regional language: `"आम्हाला फ्युएल सेल कोटिंगसाठी नोझल पाहिजे"` (Marathi) or `"हमें फ्यूल सेल कोटिंग के लिए नोजल चाहिए"` (Hindi).
2. Assistant immediately switches language, maintaining engineering units (`cP`, `ml/min`, `µm`, `kHz`).
3. Provide high viscosity parameters: `"प्लॅटिनम कार्बन स्लरी, viscosity 300 cP, flow rate 2 ml/min"`
4. Assistant recommends **High Viscosity Conical Nozzle at 60 kHz / 24 kHz** (designed for slurries up to 1000 cP).
5. Complete lead capture in regional language with quotation dispatch.

See `sample_outputs/demo_transcripts.md` and `PRESENTATION_GUIDE.md` for complete conversation transcripts and presentation notes.
