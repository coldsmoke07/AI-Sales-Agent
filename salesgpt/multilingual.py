"""
salesgpt.multilingual
=====================
Multilingual speech and text support for WaveNxD AI Sales Representative.
Supports:
- English (default, 'en')
- Marathi ('mr')
- Hindi ('hi')
- Tamil ('ta')

Retains technical terms and engineering units (viscosity, flow rate, droplet size, cP, µm, kHz, ml/min)
naturally in script or transliteration rather than confusing literal translations.
"""

import re
from typing import Dict


def detect_language(text: str, current_lang: str = "en") -> str:
    """
    Detects whether the incoming message is in Marathi, Hindi, Tamil, or English.
    Handles Devanagari script, Tamil script, and transliterated roman script.
    """
    t = text.lower()

    # Explicit switch commands
    if any(w in t for w in ["speak in english", "switch to english", "in english", "english please"]):
        return "en"
    if any(w in t for w in ["marathi", "मराठी", "marathit", "aamhala", "mala ", "tumhi", "aahe", "kasa", "mahiti", "sangitla", "nozzle badal", "sangaa"]):
        return "mr"
    if any(w in t for w in ["tamil", "தமிழ்", "vanakkam", "eppadi", "vendum", "solunga"]):
        return "ta"
    if any(w in t for w in ["hindi", "हिंदी", "हिन्दी", "namaste", "mujhe", "chahiye", "kya hai", "bataiye", "aapka", "humara", "kripya"]):
        return "hi"

    # Script inspection
    for ch in text:
        code = ord(ch)
        # Tamil Unicode Block (0x0B80 - 0x0BFF)
        if 0x0B80 <= code <= 0x0BFF:
            return "ta"
        # Devanagari Unicode Block (0x0900 - 0x097F)
        if 0x0900 <= code <= 0x097F:
            # Check for distinctive Marathi words/suffixes
            marathi_markers = ["आहे", "आम्हाला", "करा", "सांगा", "माहिती", "कसे", "व्हिस्कोसिटी", "तुम्ही", "पाहिजे"]
            if any(m in text for m in marathi_markers):
                return "mr"
            return "hi" if current_lang != "mr" else "mr"

    return current_lang or "en"


LOCALIZED_MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "greeting": (
            "Hello, I am Arjun Kulkarni from WaveNxD Technologies Pvt. Ltd., based in Kolhapur, Maharashtra. "
            "I assist engineering and manufacturing teams with our precision ultrasonic spray nozzle systems.\n\n"
            "Our ultrasonic nozzles create a soft, low-velocity spray with fine, highly uniform droplets without requiring hydraulic pressure, "
            "serving medical devices, pharmaceuticals, electronics, energy, and semiconductor applications.\n\n"
            "To get started, which industry and specific application are you working on?"
        ),
        "ask_viscosity": "What is the viscosity of your liquid in cP (centipoise)?",
        "ask_flow_rate": "What feed or flow rate do you require (in ml/min or µl)?",
        "ask_droplet_size": "What is your target droplet size requirement (in µm)?",
        "ask_contact": (
            "I would be glad to prepare an official quotation. Could you please share your Name, Company, "
            "Email Address, Phone Number, and your preferred date and time for a technical follow-up call?"
        ),
        "unlisted_info": "I will confirm this with the WaveNxD engineering team.",
        "pricing_info": "Pricing depends on the exact system integration, generator, and mounting setup. I will have our sales engineering team include full pricing in your quotation.",
    },
    "mr": {
        "greeting": (
            "नमस्कार! मी अर्जुन कुलकर्णी, WaveNxD Technologies Pvt. Ltd., कोल्हापूर येथून. "
            "आमच्या प्रिसिजन नो-प्रेशर अल्ट्रासोनिक स्प्रे नोझल सिस्टीम्ससाठी मी आपले स्वागत करतो.\n\n"
            "आमचे अल्ट्रासोनिक नोझल्स कोणत्याही हायड्रॉलिक प्रेशरशिवाय अतिसूक्ष्म आणि एकसमान ड्रॉपलेट्सचा मऊ स्प्रे तयार करतात, "
            "जे मेडिकल डिव्हाइसेस, फार्मास्युटिकल्स, इलेक्ट्रॉनिक्स, एनर्जी आणि सेमीकंडक्टर उद्योगांमध्ये वापरले जातात.\n\n"
            "सुरुवात करण्यासाठी, आपण कोणत्या इंडस्ट्री आणि ॲप्लिकेशनसाठी नोझल शोधत आहात?"
        ),
        "ask_viscosity": "आपल्या लिक्विडची व्हिस्कोसिटी (Viscosity) cP (centipoise) मध्ये किती आहे?",
        "ask_flow_rate": "आपल्याला किती फ्लो रेट / फीड रेट (Flow Rate in ml/min किंवा µl) आवश्यक आहे?",
        "ask_droplet_size": "आपल्याला अपेक्षित ड्रॉपलेट साईज (Target Droplet Size in µm) किती आहे?",
        "ask_contact": (
            "मी आपल्यासाठी WaveNxD चे अधिकृत कोटेशन (Quotation) ईमेलद्वारे पाठवतो. कृपया आपले नाव, "
            "कंपनीचे नाव, ईमेल आयडी, फोन नंबर आणि फॉलो-अप कॉलसाठी आपली सोयीची तारीख व वेळ सांगावी."
        ),
        "unlisted_info": "या तपशिलाबाबत मी WaveNxD च्या इंजिनिअरिंग टीमशी चर्चा करून आपल्याला माहिती देईन.",
        "pricing_info": "किंमत सिस्टीम इंटिग्रेशन आणि जनरेटर सेटअपवर अवलंबून असते. आमची सेल्स टीम कोटेशनमध्ये सर्व दर समाविष्ट करेल.",
    },
    "hi": {
        "greeting": (
            "नमस्ते! मैं अर्जुन कुलकर्णी, WaveNxD Technologies Pvt. Ltd., कोल्हापुर से। "
            "हमारे प्रिसिजन नो-प्रेशर अल्ट्रासोनिक स्प्रे नोजल सिस्टम्स के लिए मैं आपका स्वागत करता हूँ।\n\n"
            "हमारे अल्ट्रासोनिक नोजल बिना किसी हाइड्रोलिक प्रेशर के बहुत बारीक और एकसमान ड्रॉपलेट्स का सॉफ्ट स्प्रे बनाते हैं, "
            "जो मेडिकल डिवाइसेज, फार्मास्यूटिकल्स, इलेक्ट्रॉनिक्स, एनर्जी और सेमीकंडक्टर इंडस्ट्रीज में उपयोग होते हैं।\n\n"
            "शुरुआत करने के लिए, आप किस इंडस्ट्री और एप्लिकेशन पर काम कर रहे हैं?"
        ),
        "ask_viscosity": "आपके लिक्विड की विस्कोसिटी (Viscosity) cP में कितनी है?",
        "ask_flow_rate": "आपको कितना फ्लो रेट / फीड रेट (Flow Rate in ml/min या µl) चाहिए?",
        "ask_droplet_size": "आपकी लक्षित ड्रॉपलेट साइज (Target Droplet Size in µm) क्या है?",
        "ask_contact": (
            "मैं आपके लिए WaveNxD का आधिकारिक कोटेशन ईमेल द्वारा भेजने की व्यवस्था करता हूँ। कृपया अपना नाम, "
            "कंपनी का नाम, ईमेल पता, फोन नंबर और फॉलो-अप कॉल के लिए पसंदीदा तारीख व समय साझा करें।"
        ),
        "unlisted_info": "मैं इस विवरण की पुष्टि WaveNxD इंजीनियरिंग टीम से करके आपको सूचित करूँगा।",
        "pricing_info": "मूल्य सटीक सिस्टम इंटीग्रेशन और माउंटिंग सेटअप पर निर्भर करता है। हमारी सेल्स टीम आपके कोटेशन में पूरा मूल्य विवरण शामिल करेगी।",
    },
    "ta": {
        "greeting": (
            "வணக்கம்! நான் அர்ஜுன் குல்கர்னி, WaveNxD Technologies Pvt. Ltd., கோலாப்பூர் நிறுவனத்திலிருந்து பேசுகிறேன். "
            "எங்கள் துல்லியமான நோ-பிரஷர் அல்ட்ராசோனிக் ஸ்ப்ரே நாசில் அமைப்புகளுக்கு தங்களை வரவேற்கிறேன்.\n\n"
            "எங்கள் நாசில்கள் குறைந்த வேகத்தில் மிக நுணுக்கமான சீரான துளிகளை உருவாக்குகின்றன. "
            "மருத்துவ சாதனங்கள், மருந்துகள், எலக்ட்ரானிக்ஸ் மற்றும் குறைக்கடத்தி துறைகளுக்கு இவை பயன்படுகின்றன.\n\n"
            "தொடங்குவதற்கு, நீங்கள் எந்த தொழில் மற்றும் பயன்பாட்டிற்கு நாசில் தேடுகிறீர்கள்?"
        ),
        "ask_viscosity": "உங்கள் திரவத்தின் விஸ்காசிட்டி (Viscosity in cP) என்ன?",
        "ask_flow_rate": "உங்களுக்கு தேவையான ஃப்ளோ ரேட் (Flow Rate in ml/min or µl) என்ன?",
        "ask_droplet_size": "உங்களுக்கு தேவையான டிராப்லெட் அளவு (Droplet Size in µm) என்ன?",
        "ask_contact": (
            "நான் உங்களுக்கு அதிகாரப்பூர்வ கொட்டேஷன் (Quotation) மின்னஞ்சலில் அனுப்புகிறேன். உங்கள் பெயர், "
            "நிறுவனத்தின் பெயர், மின்னஞ்சல், தொலைபேசி எண் மற்றும் ஆலோசனை அழைப்பிற்கான நேரத்தை தெரிவிக்கவும்."
        ),
        "unlisted_info": "இந்த விவரத்தை நான் WaveNxD பொறியியல் குழுவிடம் உறுதி செய்து உங்களுக்கு தெரிவிக்கிறேன்.",
        "pricing_info": "விலை துல்லியமான அமைப்பு ஒருங்கிணைப்பைப் பொறுத்தது. எங்கள் விற்பனைக் குழு கொட்டேஷனில் முழு விவரங்களையும் வழங்கும்.",
    },
}


def get_localized_message(key: str, lang: str = "en") -> str:
    lang_dict = LOCALIZED_MESSAGES.get(lang, LOCALIZED_MESSAGES["en"])
    return lang_dict.get(key, LOCALIZED_MESSAGES["en"].get(key, ""))
