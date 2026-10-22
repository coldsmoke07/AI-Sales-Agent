"""
salesgpt.agent
==============
Context-Aware AI Sales Agent for WaveNxD Technologies Pvt. Ltd., Kolhapur.
Implements the 7-stage sales sequence with dual execution modes:
1. Built-in Deterministic Engine: Zero external API keys needed, 100% catalog compliant, zero crashes.
2. Optional LLM Engine: Connects to Gemini, OpenAI, or Groq when an API key is provided.
"""

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from salesgpt.catalog import WaveNxDCatalog
from salesgpt.multilingual import detect_language, get_localized_message
from salesgpt.stages import ConversationStage
from salesgpt.tools import generate_ics_calendar_invite, search_product_catalog, send_quotation_email

catalog = WaveNxDCatalog()

SYSTEM_PROMPT = """You are Arjun Kulkarni, an expert, consultative technical sales representative for WaveNxD Technologies Pvt. Ltd., based in Kolhapur, Maharashtra. WaveNxD designs and manufactures precision, no-pressure ultrasonic spray nozzle systems. Your primary objective is to engage prospective clients in natural, multi-turn technical dialogues, discover their application requirements, recommend the exact matching nozzle system from the WaveNxD catalog, and book next steps (quotations and follow-up calls).

STRICT FORMATTING RULE: Never use any emojis or emoticons in your responses. Use clear, professional plain text and structured bullet points when appropriate.

==================================================
1. STRICT OPERATING PRINCIPLES & GUARDRAILS
==================================================
- Single Source of Truth: The WaveNxD product catalog is your absolute source of truth.
- Anti-Hallucination Policy: NEVER invent specifications, model numbers, pricing, warranties, or delivery times.
- Missing Information Handling: If a client asks for a detail, price, warranty, or timeline not present in the catalog, state explicitly: "I will confirm this with the WaveNxD engineering team."
- Model Number Protocol: Catalog model numbers are unassigned; identify and recommend systems strictly by frequency, type/family, and primary application. Note: The 180 kHz row is mislabeled as 60 kHz in the raw catalog table; treat it strictly as 180 kHz.
- Non-Scripted Conversational Persona: Sound like a knowledgeable, polite human sales engineer, not an automated menu. Be concise, technically precise, and consultative. Never use emojis.

==================================================
2. MULTILINGUAL & LOCALIZATION RULES
==================================================
- Default Language: English.
- Dynamic Language Switching: If the client selects or speaks in an Indian regional language (such as Marathi, Hindi, or Tamil), switch immediately and respond entirely in that language.
- Technical Transliteration: Retain engineering terms and metric units naturally in script/transliteration (e.g., use natural phrasing for "viscosity", "flow rate", "droplet size", "cP", "µm", "kHz", "ml/min") rather than using awkward or archaic literal translations.

==================================================
3. CONVERSATIONAL SEQUENCE (7-STEP FLOW)
==================================================
Follow this sequence smoothly across turns:
1. Greet and Introduce: State your name (Arjun Kulkarni), confirm you represent WaveNxD Technologies Pvt. Ltd., Kolhapur, and explain that you assist with ultrasonic spray nozzle systems.
2. Pitch Briefly: In 2 to 3 sentences, explain what an ultrasonic nozzle does: it creates a soft, low-velocity spray with fine, highly uniform droplets without requiring hydraulic pressure. Highlight key target industries: medical devices, electronics, pharmaceuticals, energy, and semiconductors.
3. Requirement Discovery: Politely gather the client's parameters:
   - Target industry and specific application
   - Liquid or coating material being sprayed
   - Liquid viscosity (in cP)
   - Required flow rate / feed rate (in ml/min or µl)
   - Target droplet size requirements (in µm)
4. Answer Questions: Accurately answer any product or engineering questions directly using catalog specs.
5. Product Recommendation: Recommend the single best-matching nozzle or complete system family (plus relevant accessories like Air-Shaping Attachments or Micro Fluid Dispensing System if applicable) and provide a clear, plain-language engineering explanation for why it fits their constraints.
6. Close & Lead Capture: Offer to send an official quotation via email. Collect:
   - Full Name
   - Company Name
   - Email Address
   - Phone Number
   - Agreed Date and Time for a technical follow-up call
7. Confirm: Provide a structured summary back to the client detailing their requirement parameters, recommended nozzle system, quotation dispatch status, and the scheduled callback slot.
"""


def extract_state_from_messages(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Scans conversation turns to extract engineering requirements, lead info, and language state.
    """
    state: Dict[str, Any] = {
        "language": "en",
        "stage": ConversationStage.INTRODUCTION.value,
        "industry": None,
        "application": None,
        "material": None,
        "viscosity_cp": None,
        "flow_rate_ml_min": None,
        "dispensing_ul": None,
        "droplet_size_um": None,
        "recommended_product": None,
        "client_name": None,
        "company": None,
        "email": None,
        "phone": None,
        "callback_time": None,
        "greeting_done": False,
    }

    for msg in messages:
        if msg.get("role") == "assistant":
            state["greeting_done"] = True
            continue

        text = msg.get("content", "")
        t = text.lower()
        state["language"] = detect_language(text, state["language"])

        # 1. Application mapping
        app_map = [
            (["stent", "drug eluting", "des coating", "implant", "स्टेंट"], "Medical Devices", "Stent coating"),
            (["blood collection", "vacutainer", "edta tube", "blood tube", "रक्त संकलन", "ब्लड ट्यूब"], "Medical Devices", "Blood collection tube coating"),
            (["syringe", "barrel coating", "silicone lubrication", "सिरिंज"], "Medical Devices", "Syringe coating"),
            (["balloon", "catheter", "कॅथेटर", "कैथेटर"], "Medical Devices", "Balloon / catheter coating"),
            (["pipac", "chemotherapy", "oncology", "peritoneal", "केमोथेरपी", "कीमोथेरेपी"], "Medical / Pharmaceuticals", "PIPAC chemotherapy"),
            (["fuel cell", "pem", "catalyst slurry", "platinum carbon", "membrane electrode", "फ्युएल सेल", "फ्यूल सेल"], "Energy", "Fuel cell coating"),
            (["hydrogen", "electrolyzer", "हायड्रोजन", "हाइड्रोजन"], "Energy", "Hydrogen production / electrolyzer coating"),
            (["powder synthesis", "nanoparticle", "पावडर", "पाउडर"], "Pharmaceuticals / Materials", "Powder synthesis"),
            (["industrial spray dry", "production spray dry", "high throughput", "औद्योगिक स्प्रे ड्रायर"], "Pharmaceuticals / Chemical", "Industrial spray drying"),
            (["lab spray dry", "laboratory spray dry", "लॅब स्प्रे ड्रायर", "लैब स्प्रे ड्रायर"], "Pharmaceuticals / R&D", "Lab spray drying"),
            (["tco", "transparent conductive", "ito", "thin film", "micro-coating", "450", "solar cell", "सेमीकंडक्टर"], "Electronics / Semiconductors", "TCO / Micro-coating (Spray Pyrolysis)"),
            (["spray pyrolysis", "pyrolysis", "स्प्रे पायरोलिसिस"], "Electronics / Materials", "Spray pyrolysis"),
        ]
        for keywords, ind, app_name in app_map:
            if any(k in t for k in keywords):
                state["industry"] = ind
                state["application"] = app_name
                break

        if not state["industry"]:
            if any(k in t for k in ["medical", "वैद्यकीय", "मेडिकल", "மருத்துவ"]):
                state["industry"] = "Medical Devices"
            elif any(k in t for k in ["pharma", "औषध", "फार्मा"]):
                state["industry"] = "Pharmaceuticals"
            elif any(k in t for k in ["electron", "इलेक्ट्रॉनिक", "सेमीकंडक्टर", "semiconductor"]):
                state["industry"] = "Electronics / Semiconductors"
            elif any(k in t for k in ["energy", "ऊर्जा", "एनर्जी", "solar", "battery"]):
                state["industry"] = "Energy"

        # 2. Materials
        materials = [
            "plga", "pdlla", "sirolimus", "paclitaxel", "heparin", "edta",
            "clot activator", "silicone oil", "platinum", "pt/c", "carbon slurry",
            "nafion", "catalyst ink", "ito", "zinc oxide", "zno", "sno2", "tco",
            "chemotherapy", "cisplatin", "doxorubicin", "slurry", "suspension",
        ]
        for m in materials:
            if m in t:
                state["material"] = m.upper() if m in ["plga", "edta", "ito", "tco"] else m.title()
                break

        # 3. Viscosity (cP)
        visc = re.search(r"(\d+(?:\.\d+)?)\s*(?:cp|centipoise|सेंटीपॉइज)", t)
        if not visc:
            visc = re.search(r"(?:viscosity|व्हिस्कोसिटी|विस्कोसिटी|गाढ़ापन)\s*(?:is|of|around|about|:|=)?\s*(\d+(?:\.\d+)?)", t)
        if visc:
            state["viscosity_cp"] = float(visc.group(1))

        # 4. Flow rate (ml/min)
        flow = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml\s*/\s*min|ml per min|ml/m|एमएल/मिनिट|एमएल/मिनट)", t)
        if not flow:
            flow = re.search(r"(?:flow rate|feed rate|फ्लो रेट|फीड रेट)\s*(?:is|of|around|about|:|=)?\s*(\d+(?:\.\d+)?)\s*(?:ml)?", t)
        if flow:
            state["flow_rate_ml_min"] = float(flow.group(1))

        # 5. Micro-dispensing (µl)
        ul = re.search(r"(\d+(?:\.\d+)?)\s*(?:ul|µl|microliter|मायक्रोलिटर|माइक्रोलिटर)", t)
        if ul:
            state["dispensing_ul"] = float(ul.group(1))
            if state["flow_rate_ml_min"] is None:
                state["flow_rate_ml_min"] = round(float(ul.group(1)) / 1000.0, 3)

        # 6. Droplet size (µm)
        drop = re.search(r"(\d+(?:\.\d+)?)\s*(?:um|µm|micron|microns|मायक्रॉन|माइक्रोन)", t)
        if not drop:
            drop = re.search(r"(?:droplet size|droplet|ड्रॉपलेट साईज|ड्रॉपलेट साइज|थेंबाचा आकार)\s*(?:is|of|around|about|:|=)?\s*(\d+(?:\.\d+)?)", t)
        if drop:
            state["droplet_size_um"] = float(drop.group(1))

        # 7. Contact Details
        email = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
        if email:
            state["email"] = email.group(1)

        phone = re.search(r"((?:\+91[\-\s]?)?[6-9]\d{9}|\b\d{3}[\-\s]?\d{3}[\-\s]?\d{4}\b)", text)
        if phone:
            state["phone"] = phone.group(1).strip()

        # Name extraction
        name_patterns = [
            r"(?:my name is|i am|this is|नाव|नाम|పేరు)\s+(?:(?:Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
            r"(?:(?:Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*,\s*(?:from|at)\s+([A-Za-z0-9\s]+)",
            r"(?:^|\n|\b)(?:Dr\.|Mr\.|Mrs\.|Ms\.)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
        ]
        for np in name_patterns:
            m = re.search(np, text)
            if m:
                state["client_name"] = m.group(1).strip()
                break

        # Company extraction
        company_m = re.search(r"(?:from|at|company|कंपनी)\s+([A-Z][a-zA-Z0-9\s]+(?:Ltd|Inc|Corp|Pvt|Technologies|MedTech|Energy|Pharma|Labs)?)", text)
        if company_m:
            state["company"] = company_m.group(1).strip()

        # Callback time
        callback_m = re.search(r"(\b(?:tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|oct(?:ober)?\s+\d{1,2}|nov(?:ember)?\s+\d{1,2})\b[^\n,.]*|\d{1,2}(?::\d{2})?\s*(?:am|pm))", t)
        if callback_m:
            state["callback_time"] = callback_m.group(1).strip().title()

    # Determine recommended product if parameters are discovered
    if state["application"] or state["industry"] or state["viscosity_cp"] is not None:
        rec_nozzle, _, _ = catalog.match_nozzle(
            application=state["application"],
            industry=state["industry"],
            material=state["material"],
            viscosity_cp=state["viscosity_cp"],
            flow_rate_ml_min=state["flow_rate_ml_min"],
            dispensing_ul=state["dispensing_ul"],
            droplet_size_um=state["droplet_size_um"],
        )
        if rec_nozzle:
            state["recommended_product"] = rec_nozzle["family"]

    # Determine current stage
    if state["email"] and state["phone"] and state["callback_time"]:
        state["stage"] = ConversationStage.CONFIRMATION.value
    elif state["recommended_product"] and any(k in [state["email"], state["client_name"], state["company"]] if k else False for k in [state["email"], state["client_name"], state["company"]]):
        state["stage"] = ConversationStage.CLOSING_QUOTATION.value
    elif state["recommended_product"] and state["viscosity_cp"] is not None:
        state["stage"] = ConversationStage.RECOMMENDATION.value
    elif state["application"] or state["industry"]:
        state["stage"] = ConversationStage.REQUIREMENT_DISCOVERY.value
    elif state["greeting_done"]:
        state["stage"] = ConversationStage.PITCH.value
    else:
        state["stage"] = ConversationStage.INTRODUCTION.value

    return state


def call_llm_provider(
    system_prompt: str,
    messages: List[Dict[str, str]],
    api_key: str,
    provider: str = "gemini",
) -> Optional[str]:
    """
    Direct HTTPS call to LLM providers (Gemini, OpenAI, Groq) using standard library urllib.
    """
    try:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            contents = []
            for m in messages:
                role = "user" if m.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": contents,
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600},
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()

        elif provider in ("openai", "groq"):
            endpoint = "https://api.openai.com/v1/chat/completions" if provider == "openai" else "https://api.groq.com/openai/v1/chat/completions"
            model_name = "gpt-4o-mini" if provider == "openai" else "llama-3.3-70b-versatile"
            formatted_msgs = [{"role": "system", "content": system_prompt}] + messages
            payload = {
                "model": model_name,
                "messages": formatted_msgs,
                "temperature": 0.2,
                "max_tokens": 600,
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
    return None


class SalesAgent:
    """
    SalesGPT Agent for WaveNxD Ultrasonic Spray Nozzle Solutions.
    """

    def __init__(self, catalog_obj: Optional[WaveNxDCatalog] = None):
        self.catalog = catalog_obj or catalog

    def run(
        self,
        messages: List[Dict[str, str]],
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a multi-turn conversation turn and returns:
        - reply: assistant message text
        - state: discovered requirements & contact details
        - stage: current conversation stage (1-7)
        - options: recommended quick-response chips for demo
        """
        state = extract_state_from_messages(messages)
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        lang = state["language"]
        t = last_user_msg.lower()

        # Handle explicit reset/restart
        if any(w in t for w in ["restart", "new conversation", "reset", "start over"]):
            return {
                "reply": get_localized_message("greeting", lang),
                "state": extract_state_from_messages([]),
                "stage": ConversationStage.INTRODUCTION.value,
                "options": self._get_initial_options(lang),
            }

        # Check for unlisted details (Anti-hallucination guardrail)
        if any(w in t for w in ["price", "cost", "how much", "किंमत", "भाव", "दर", "விலை", "rate"]):
            reply = get_localized_message("pricing_info", lang)
            return {"reply": reply, "state": state, "stage": state["stage"], "options": []}

        if any(w in t for w in ["delivery time", "warranty", "guarantee", "lead time", "वारंटी", "डिलिव्हरी"]):
            reply = (
                "WaveNxD warranty and delivery timelines vary depending on whether it is a standard nozzle "
                "or a custom system integration. " + get_localized_message("unlisted_info", lang)
            )
            return {"reply": reply, "state": state, "stage": state["stage"], "options": []}

        # If an LLM API key is available, attempt LLM call
        active_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
        active_prov = provider or ("gemini" if os.getenv("GEMINI_API_KEY") else ("openai" if os.getenv("OPENAI_API_KEY") else "groq"))

        if active_key and active_prov:
            llm_reply = call_llm_provider(SYSTEM_PROMPT, messages, active_key, active_prov)
            if llm_reply:
                # Remove emojis if any leaked
                clean_reply = re.sub(r"[\U00010000-\U0010ffff]", "", llm_reply)
                return {
                    "reply": clean_reply,
                    "state": state,
                    "stage": state["stage"],
                    "options": self._generate_context_options(state, lang),
                }

        # Deterministic Consultative Engine (Zero-Crash Evaluation Mode)
        deterministic_reply, options = self._deterministic_reply(state, last_user_msg, lang)
        return {
            "reply": deterministic_reply,
            "state": state,
            "stage": state["stage"],
            "options": options,
        }

    def _get_initial_options(self, lang: str) -> List[str]:
        if lang == "mr":
            return [
                "मेडिकल डिव्हाइसेस - स्टेंट कोटिंग (Stent Coating)",
                "मेडिकल डिव्हाइसेस - सिरिंज कोटिंग (Syringe Coating)",
                "एनर्जी - फ्युएल सेल कोटिंग (Fuel Cell Slurry)",
                "फार्मा - लॅब स्प्रे ड्रायर (Lab Spray Dryer)",
                "Switch to English",
            ]
        elif lang == "hi":
            return [
                "मेडिकल डिवाइसेज - स्टेंट कोटिंग (Stent Coating)",
                "एनर्जी - फ्यूल सेल कोटिंग (Fuel Cell Coating)",
                "इलेक्ट्रॉनिक्स - स्प्रे पायरोलिसिस (TCO Coating)",
                "औद्योगिक स्प्रे ड्रायर (High Flow)",
                "Switch to English",
            ]
        elif lang == "ta":
            return [
                "மருத்துவ சாதனங்கள் - ஸ்டென்ட் பூச்சு (Stent Coating)",
                "எரிசக்தி - எரிபொருள் செல் (Fuel Cell)",
                "Switch to English",
            ]
        return [
            "Medical Devices - Stent Coating",
            "Medical Devices - Syringe Coating",
            "Medical Devices - Blood Collection Tubes",
            "Energy - Fuel Cell Coating",
            "Pharma / R&D - Lab Spray Dryer",
            "Industrial Spray Dryer (High Flow)",
            "Electronics - TCO / Spray Pyrolysis",
            "मराठीत बोला (Switch to Marathi)",
            "हिंदी में बात करें (Switch to Hindi)",
            "தமிழில் பேசுங்கள் (Switch to Tamil)",
        ]

    def _generate_context_options(self, state: Dict[str, Any], lang: str) -> List[str]:
        if not state["material"]:
            return ["Polymer drug solution (< 10 cP)", "Silicone oil (350 cP)", "Catalyst carbon slurry (300 cP)", "Aqueous precursor (< 5 cP)"]
        if state["viscosity_cp"] is None:
            return ["Viscosity is 5 cP", "Viscosity is 15 cP", "Viscosity is 300 cP (high viscosity)", "Viscosity is 800 cP"]
        if state["flow_rate_ml_min"] is None and state["dispensing_ul"] is None:
            return ["Flow rate is 3 ml/min", "Flow rate is 5 ml/min", "Flow rate is 20 ml/min", "Dispensing volume 50 µl"]
        if state["droplet_size_um"] is None:
            return ["Droplet size 10 µm (Ultra-fine)", "Droplet size 25 µm", "Droplet size 40 µm", "Droplet size 60 µm"]
        if not state["email"]:
            return ["Email: rahul.sharma@medtech-labs.in, Phone: 9876543210, Call: Tomorrow 11 AM"]
        return ["Confirm and Download Calendar Invite (.ics)", "Send Official Quotation Email"]

    def _deterministic_reply(
        self,
        state: Dict[str, Any],
        user_msg: str,
        lang: str,
    ) -> Tuple[str, List[str]]:
        t = user_msg.lower()

        # Step 7: Confirmation & Summary
        if state["email"] and (state["phone"] or state["callback_time"]):
            rec_nozzle, accessories, rationale = catalog.match_nozzle(
                application=state["application"],
                industry=state["industry"],
                material=state["material"],
                viscosity_cp=state["viscosity_cp"],
                flow_rate_ml_min=state["flow_rate_ml_min"],
                dispensing_ul=state["dispensing_ul"],
                droplet_size_um=state["droplet_size_um"],
            )
            nozzle_title = rec_nozzle["family"] if rec_nozzle else "Standard Family Ultrasonic Nozzle"

            if lang == "mr":
                summary = (
                    f"धन्यवाद {state['client_name'] or 'ग्राहक महोदय'}! आपल्या अर्जाचा सारांश खालीलप्रमाणे आहे:\n\n"
                    f"• उद्योग व ॲप्लिकेशन: {state['industry'] or 'N/A'} - {state['application'] or 'N/A'}\n"
                    f"• लिक्विड / मटेरियल: {state['material'] or 'Specified fluid'}\n"
                    f"• ऑपरेटिंग पॅरामीटर्स: Viscosity: {state['viscosity_cp'] or '< 50'} cP | Flow Rate: {state['flow_rate_ml_min'] or '5'} ml/min | Droplet Size: {state['droplet_size_um'] or '40'} µm\n"
                    f"• शिफारस केलेले नोझल: {nozzle_title}\n"
                    f"• पाठवण्याचे तपशील: {state['email']} | {state['phone'] or 'N/A'}\n"
                    f"• शेड्यूल केलेला कॉल: {state['callback_time'] or 'उद्या सकाळी ११:०० वाजता'}\n\n"
                    f"मी WaveNxD चे अधिकृत कोटेशन आपल्या ईमेलवर पाठवले आहे आणि फॉलो-अप कॉल शेड्यूल केला आहे. WaveNxD शी संपर्क केल्याबद्दल धन्यवाद!"
                )
            elif lang == "hi":
                summary = (
                    f"धन्यवाद {state['client_name'] or 'महोदय'}! आपके परामर्श का सारांश नीचे दिया गया है:\n\n"
                    f"• इंडस्ट्री व एप्लिकेशन: {state['industry'] or 'N/A'} - {state['application'] or 'N/A'}\n"
                    f"• लिक्विड मटेरियल: {state['material'] or 'Specified fluid'}\n"
                    f"• ऑपरेटिंग पैरामीटर्स: Viscosity: {state['viscosity_cp'] or '< 50'} cP | Flow Rate: {state['flow_rate_ml_min'] or '5'} ml/min | Droplet Size: {state['droplet_size_um'] or '40'} µm\n"
                    f"• अनुशंसित नोजल: {nozzle_title}\n"
                    f"• कोटेशन ईमेल: {state['email']} | फोन: {state['phone'] or 'N/A'}\n"
                    f"• तकनीकी कॉल: {state['callback_time'] or 'कल 11:00 AM'}\n\n"
                    f"WaveNxD का आधिकारिक कोटेशन आपके ईमेल पर प्रेषित कर दिया गया है। WaveNxD से जुड़ने के लिए धन्यवाद!"
                )
            else:
                summary = (
                    f"Thank you, {state['client_name'] or 'Valued Client'}! Here is the confirmed summary of your consultation:\n\n"
                    f"==================================================\n"
                    f"WAVENXD TECHNICAL CONSULTATION SUMMARY\n"
                    f"==================================================\n"
                    f"• Client: {state['client_name'] or 'Engineering Lead'} ({state['company'] or 'Client Facility'})\n"
                    f"• Industry & Application: {state['industry'] or 'N/A'} - {state['application'] or 'N/A'}\n"
                    f"• Liquid Material: {state['material'] or 'Specified formulation'}\n"
                    f"• Viscosity: {state['viscosity_cp'] or '< 50'} cP\n"
                    f"• Flow Rate: {state['flow_rate_ml_min'] or '5'} ml/min (Dispensing: {state['dispensing_ul'] or 'N/A'} µl)\n"
                    f"• Droplet Size: {state['droplet_size_um'] or '40'} µm\n"
                    f"• Recommended System: {nozzle_title}\n"
                    f"• Quotation Dispatch: Queued to {state['email']}\n"
                    f"• Scheduled Callback Slot: {state['callback_time'] or 'Tomorrow at 11:00 AM'}\n"
                    f"==================================================\n\n"
                    f"Our senior applications engineer will connect with you at the confirmed slot. "
                    f"You can also download your calendar invite below."
                )
            return summary, ["Download Calendar Invite (.ics)", "New Conversation"]

        # Step 6: Close & Contact Collection
        if state["recommended_product"] and (
            state["viscosity_cp"] is not None or "recommend" in t or "quote" in t or "quotation" in t or "proceed" in t
        ):
            rec_nozzle, accessories, rationale = catalog.match_nozzle(
                application=state["application"],
                industry=state["industry"],
                material=state["material"],
                viscosity_cp=state["viscosity_cp"],
                flow_rate_ml_min=state["flow_rate_ml_min"],
                dispensing_ul=state["dispensing_ul"],
                droplet_size_um=state["droplet_size_um"],
            )

            acc_note = ""
            if accessories:
                acc_names = ", ".join([a["name"] for a in accessories])
                acc_note = f"\n\nComplete System Integration: We also recommend pairing this with WaveNxD's {acc_names} ({accessories[0]['specifications']})."

            if lang == "mr":
                reply = (
                    f"आपल्या ॲप्लिकेशनसाठी WaveNxD कॅटलॉगमधून सर्वोत्तम शिफारस:\n\n"
                    f"**{rec_nozzle['family']}**\n"
                    f"• ऑपरेटिंग फ्रिक्वेन्सी: {rec_nozzle['frequency_khz']} kHz\n"
                    f"• ड्रॉपलेट साईज: {rec_nozzle['droplet_size_um']} µm\n"
                    f"• फीड रेट: {rec_nozzle['feed_rate_text']}\n"
                    f"• कमाल व्हिस्कोसिटी मर्यादा: {rec_nozzle['viscosity_text']}\n\n"
                    f"तांत्रिक कारण: {rationale}{acc_note}\n\n"
                    f"{get_localized_message('ask_contact', lang)}"
                )
            elif lang == "hi":
                reply = (
                    f"आपके एप्लिकेशन के लिए WaveNxD कैटलॉग से सर्वश्रेष्ठ अनुशंसा:\n\n"
                    f"**{rec_nozzle['family']}**\n"
                    f"• ऑपरेटिंग फ्रीक्वेंसी: {rec_nozzle['frequency_khz']} kHz\n"
                    f"• ड्रॉपलेट साइज: {rec_nozzle['droplet_size_um']} µm\n"
                    f"• फीड रेट: {rec_nozzle['feed_rate_text']}\n"
                    f"• अधिकतम विस्कोसिटी सीमा: {rec_nozzle['viscosity_text']}\n\n"
                    f"तकनीकी कारण: {rationale}{acc_note}\n\n"
                    f"{get_localized_message('ask_contact', lang)}"
                )
            else:
                reply = (
                    f"Based on your requirements, here is the recommended WaveNxD solution:\n\n"
                    f"**{rec_nozzle['family']}**\n"
                    f"• Operating Frequency: {rec_nozzle['frequency_khz']} kHz\n"
                    f"• Droplet Size: {rec_nozzle['droplet_size_um']} µm\n"
                    f"• Feed Rate: {rec_nozzle['feed_rate_text']}\n"
                    f"• Viscosity Rating: {rec_nozzle['viscosity_text']}\n\n"
                    f"Technical Justification: {rationale}{acc_note}\n\n"
                    f"{get_localized_message('ask_contact', lang)}"
                )
            return reply, [
                "Dr. Amit Patil, StentTech Labs, amit@stenttech.in, +91 9822012345, Tomorrow 11:00 AM",
                "Rajesh Verma, FuelCell Dynamics, rajesh@fuelcelldyn.com, 9890123456, Friday 3:00 PM",
            ]

        # Step 3 & 4: Requirement Discovery
        if state["application"] or state["industry"]:
            if lang == "mr":
                missing_mr = []
                if not state["material"]:
                    missing_mr.append("स्प्रे केले जाणारे लिक्विड किंवा कोटिंग मटेरियल (Liquid/Material)")
                if state["viscosity_cp"] is None:
                    missing_mr.append("लिक्विडची व्हिस्कोसिटी (Viscosity in cP)")
                if state["flow_rate_ml_min"] is None and state["dispensing_ul"] is None:
                    missing_mr.append("अपेक्षित फ्लो रेट किंवा डिस्पेंसिंग व्हॉल्युम (Flow Rate in ml/min किंवा µl)")
                if state["droplet_size_um"] is None:
                    missing_mr.append("अपेक्षित ड्रॉपलेट साईज (Droplet Size in µm)")
                bullets = "\n".join([f"• {m}" for m in missing_mr])
                reply = (
                    f"WaveNxD च्या कॅटलॉगमधून योग्य नोझल सिस्टीम निवडण्यासाठी, कृपया खालील माहिती सांगा:\n"
                    f"{bullets}\n\nआपण साधारण आकडेवारी देऊ शकता."
                )
            elif lang == "hi":
                missing_hi = []
                if not state["material"]:
                    missing_hi.append("स्प्रे किए जाने वाला लिक्विड या कोटिंग मटेरियल (Liquid/Material)")
                if state["viscosity_cp"] is None:
                    missing_hi.append("लिक्विड की विस्कोसिटी (Viscosity in cP)")
                if state["flow_rate_ml_min"] is None and state["dispensing_ul"] is None:
                    missing_hi.append("अपेक्षित फ्लो रेट या डिस्पेंसिंग वॉल्यूम (Flow Rate in ml/min या µl)")
                if state["droplet_size_um"] is None:
                    missing_hi.append("अपेक्षित ड्रॉपलेट साइज (Droplet Size in µm)")
                bullets = "\n".join([f"• {m}" for m in missing_hi])
                reply = (
                    f"WaveNxD कैटलॉग से सटीक नोजल सिस्टम चुनने के लिए, कृपया निम्नलिखित जानकारी साझा करें:\n"
                    f"{bullets}\n\nआप अनुमानित मान भी प्रदान कर सकते हैं।"
                )
            else:
                missing = []
                if not state["material"]:
                    missing.append("liquid or coating material being sprayed")
                if state["viscosity_cp"] is None:
                    missing.append("liquid viscosity (in cP)")
                if state["flow_rate_ml_min"] is None and state["dispensing_ul"] is None:
                    missing.append("required flow or dispensing rate (in ml/min or µl)")
                if state["droplet_size_um"] is None:
                    missing.append("target droplet size (in µm)")
                bullets = "\n".join([f"• {m}" for m in missing])
                reply = (
                    f"To match the exact nozzle system from the WaveNxD catalog for {state['application'] or state['industry']}, "
                    f"could you please share:\n{bullets}"
                )
            return reply, self._generate_context_options(state, lang)

        # Default Greeting & Pitch (Step 1 & 2)
        return get_localized_message("greeting", lang), self._get_initial_options(lang)
