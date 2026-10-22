# Live Demo & Presentation Guide (15 Marks)

Use these notes during your live evaluation presentation and Q&A.

## 1. Architecture Overview
- **Single Source of Truth (`catalog.json`)**: All 9 ultrasonic nozzle configurations and 3 companion systems/attachments (`Micro Fluid Dispensing System`, `PLC-Controlled XY Spray Pyrolysis System`, and `Air-Shaping Attachments`) are structured in `catalog.json`.
- **Hybrid Sales Engine (`sales_engine.py`)**:
  - **Parameter Tracker**: Extracts and validates the 5 technical parameters (industry/application, material, viscosity in `cP`, flow rate in `ml/min` or `µl`, and droplet size in `µm`) plus the 5 lead-capture fields (name, company, email, phone, and follow-up date/time) across turns.
  - **Deterministic Engineering Matcher + LLM Layer**: Supports live LLM calls (`Gemini 2.5 Flash`, `GPT-4o-mini`, or `Llama 3.3 70B`) governed by a strict system prompt, paired with a deterministic fallback engine so the live demo never crashes due to network or API rate limits.
- **ChatGPT-Style Frontend (`templates/index.html`, `static/script.js`)**: Minimalist interface with real-time parameter tracking badges, Web Speech API microphone input (`en-IN`, `mr-IN`, `hi-IN`, `ta-IN`), and speech synthesis output.

## 2. How Product Knowledge is Loaded & Guardrailed
- Model numbers are intentionally omitted because the catalog leaves the model number column unassigned; products are identified strictly by **frequency**, **family/type**, and **application**.
- The `180 kHz Standard Torch` row (mislabeled as `60KHz` in the raw catalog table) is normalized to `180 kHz` based on its heading.
- **Anti-Hallucination Guardrails**:
  - Pricing queries always trigger: *"Pricing depends on the exact system integration, generator, and mounting setup. I will have our sales engineering team include full pricing in your quotation."*
  - Unlisted specifications (warranty, delivery lead time, power consumption) always trigger: *"I will confirm this with the WaveNxD engineering team."*
  - Viscosities above `1000 cP` trigger an engineering boundary warning explaining that WaveNxD's High Viscosity Conical and 25 mm Extended Horn nozzles are rated up to `1000 cP`.

## 3. Live Demo Walkthrough (2 Required Scenarios)

### Scenario A: Medical Stent Coating Client (English)
1. Click **Scenario 1: Medical Stent Coating** in the left sidebar (or type the message manually).
2. The assistant identifies **Standard Torch (180 kHz, 10 µm droplets, 5 ml/min, < 50 cP)** paired with the **Micro Fluid Dispensing System (0 to 200 µl)** and explains why low-velocity 10 µm droplets prevent polymer bridging on stent struts.
3. Ask a follow-up question: *"What is the price and warranty of this system?"* -> Assistant applies the exact catalog pricing and engineering confirmation rules.
4. Provide test contact details to close:
   `Dr.ohan Mehta, Mehta MedTech Pvt Ltd, rohan@mehtamedtech.in, 9876543210, Friday 24 Oct at 11:00 AM`
5. The assistant outputs the complete **Step 7 Confirmation Summary**.

### Scenario B: Fuel Cell Client Switching to Marathi / Hindi
1. Click **New Conversation**, then click **Scenario 2: Fuel Cell (Marathi Switch)** (or type in Marathi/Hindi).
2. The assistant immediately switches to Marathi while keeping engineering units (`450 cP`, `2.5 ml/min`, `40 µm`, `60 kHz`) natural, and recommends the **High Viscosity, Conical (60 kHz)** nozzle (`< 1000 cP`, `up to 3 ml/min`).
3. Provide test contact details:
   `Sanket Patil, Sahyadri Energy Systems, sanket@sahyadrienergy.in, 9823011223, Tomorrow 4:00 PM`
4. The assistant delivers the full confirmation summary in Marathi.

## 4. Main Challenges & Future Improvements (For Evaluator Q&A)
- **Main Challenges Solved**:
  1. Avoiding hallucinated specs or awkward literal translations of technical units (`cP`, `µm`, `kHz`, `ml/min`) when switching into Marathi, Hindi, or Tamil.
  2. Ensuring natural multi-turn state tracking when a client provides partial parameters across multiple messages.
- **What We Would Improve Next**:
  1. Integrate automated PDF datasheet attachment generation per nozzle family.
  2. Connect lead capture confirmation directly to WaveNxD's CRM and Google Calendar API.
