(function () {
  var messages = [];
  var ttsEnabled = false;
  var recognition = null;
  var isRecording = false;
  var lastState = null;

  var chatStream = document.getElementById("chatStream");
  var chatForm = document.getElementById("chatForm");
  var userInput = document.getElementById("userInput");
  var btnNewChat = document.getElementById("btnNewChat");
  var btnMic = document.getElementById("btnMic");
  var btnCancelMic = document.getElementById("btnCancelMic");
  var micStatusBanner = document.getElementById("micStatusBanner");
  var micStatusText = document.getElementById("micStatusText");
  var btnToggleTTS = document.getElementById("btnToggleTTS");
  var voiceLangSelect = document.getElementById("voiceLangSelect");

  var catalogModal = document.getElementById("catalogModal");
  var btnOpenCatalog = document.getElementById("btnOpenCatalog");
  var btnCloseCatalog = document.getElementById("btnCloseCatalog");

  var INITIAL_GREETING =
    "Hello, I am Arjun Kulkarni from WaveNxD Technologies Pvt. Ltd., based in Kolhapur, Maharashtra. " +
    "I assist engineering and manufacturing teams with our precision ultrasonic spray nozzle systems.\n\n" +
    "Our ultrasonic nozzles create a soft, low-velocity spray with fine, highly uniform droplets without requiring hydraulic pressure, serving medical devices, pharmaceuticals, electronics, energy, and semiconductor applications.\n\n" +
    "To get started, which industry and specific application are you working on? You can pick an option below or type your own.";

  var INITIAL_OPTIONS_EN = [
    "Medical Devices - Stent Coating",
    "Medical Devices - Syringe Coating",
    "Medical Devices - Blood Collection Tubes",
    "Medical - PIPAC Chemotherapy",
    "Energy - Fuel Cell Coating",
    "Energy - Hydrogen Production",
    "Pharma / R&D - Lab Spray Dryer",
    "Industrial Spray Dryer (High Flow)",
    "Electronics - TCO / Spray Pyrolysis",
    "मराठीत बोला (Switch to Marathi)",
    "हिंदी में बात करें (Switch to Hindi)",
    "தமிழில் பேசவும் (Switch to Tamil)"
  ];

  function detectLanguage(text, currentLang) {
    var t = text.toLowerCase();
    if (/marathi|मराठी|aamhala|mala |tumhi|aahe|sangitla|कसे|आहे|मला|आम्हाला|साठी|कृपया|सांगा/.test(text.toLowerCase())) {
      return "mr";
    }
    if (/tamil|தமிழ்|vanakkam|vendum|[\u0B80-\u0BFF]/.test(text)) {
      return "ta";
    }
    if (/hindi|हिंदी|हिन्दी|namaste|mujhe|chahiye|bataiye|[\u0900-\u097F]/.test(text)) {
      if (/आहे|मला|आम्हाला|तुम्ही|साठी|कृपया|सांगा/.test(text)) return "mr";
      return currentLang === "mr" ? "mr" : "hi";
    }
    if (/in english|switch to english|speak english/.test(t)) {
      return "en";
    }
    return currentLang || "en";
  }

  function getLastBotQuestionStep(state) {
    if (!state.application && !state.industry) return "app";
    if (!state.material) return "material";
    if (state.viscosity_cp === null) return "viscosity";
    if (state.flow_rate_ml_min === null && state.dispensing_ul === null) return "flow";
    if (state.droplet_size_um === null) return "droplet";
    if (!state.client_name || !state.email || !state.phone || !state.callback_time) return "lead";
    return "done";
  }

  function extractState(msgList) {
    var langFromDropdown = (voiceLangSelect && voiceLangSelect.value) ? voiceLangSelect.value.slice(0, 2) : "en";
    var state = {
      language: langFromDropdown,
      industry: null,
      application: null,
      material: null,
      viscosity_cp: null,
      flow_rate_ml_min: null,
      dispensing_ul: null,
      droplet_size_um: null,
      recommended_product: null,
      client_name: null,
      company: null,
      email: null,
      phone: null,
      callback_time: null
    };

    for (var i = 0; i < msgList.length; i++) {
      var m = msgList[i];
      if (m.role !== "user") continue;
      var text = (m.content || "").trim();
      var t = text.toLowerCase();
      state.language = detectLanguage(text, state.language);

      var expectedStep = getLastBotQuestionStep(state);

      // 1. Application & Industry matching
      if (/stent|drug eluting|implant|स्टेंट/.test(t)) {
        state.industry = "Medical Devices";
        state.application = "Stent coating";
      } else if (/blood collection|vacutainer|blood tube|रक्त संकलन|ब्लड ट्यूब/.test(t)) {
        state.industry = "Medical Devices";
        state.application = "Blood collection tube coating";
      } else if (/syringe|barrel|सिरिंज/.test(t)) {
        state.industry = "Medical Devices";
        state.application = "Syringe coating";
      } else if (/balloon|catheter|कॅथेटर|कैथेटर/.test(t)) {
        state.industry = "Medical Devices";
        state.application = "Balloon / catheter coating";
      } else if (/pipac|chemotherapy|oncology|केमोथेरपी|कीमोथेरेपी/.test(t)) {
        state.industry = "Medical / Pharmaceuticals";
        state.application = "PIPAC chemotherapy";
      } else if (/fuel cell|pem|catalyst slurry|फ्युएल सेल|फ्यूल सेल/.test(t)) {
        state.industry = "Energy";
        state.application = "Fuel cell coating";
      } else if (/hydrogen|electrolyzer|हायड्रोजन|हाइड्रोजन/.test(t)) {
        state.industry = "Energy";
        state.application = "Hydrogen production";
      } else if (/powder synthesis|nanoparticle|पावडर|पाउडर/.test(t)) {
        state.industry = "Pharmaceuticals / Materials";
        state.application = "Powder synthesis";
      } else if (/industrial spray dry|high flow|high throughput|औद्योगिक स्प्रे ड्रायर/.test(t)) {
        state.industry = "Pharmaceuticals / Chemical";
        state.application = "Industrial spray drying";
      } else if (/lab spray dry|लॅब स्प्रे|लैब स्प्रे/.test(t)) {
        state.industry = "Pharmaceuticals / R&D";
        state.application = "Lab spray drying";
      } else if (/tco|transparent conductive|ito|micro-coating|450|semiconductor|सेमीकंडक्टर/.test(t)) {
        state.industry = "Electronics / Semiconductors";
        state.application = "TCO / Micro-coating (Spray Pyrolysis)";
      } else if (/spray pyrolysis|pyrolysis|पायरोलिसिस/.test(t)) {
        state.industry = "Electronics / Materials";
        state.application = "Spray pyrolysis";
      } else if (expectedStep === "app" && !/marathi|मराठी|hindi|हिंदी|हिन्दी|tamil|தமிழ்|hi\b|hello\b|namaste|namaskar|price|cost|switch to/.test(t) && text.length > 2) {
        state.industry = "Specified Industry";
        state.application = text;
      }

      // 2. Material matching
      var knownMats = [
        "plga drug-polymer solution", "sirolimus polymer coating", "pdlla solution", "plga", "drug-polymer",
        "sirolimus", "paclitaxel", "pdlla", "polymer", "heparin solution", "edta anticoagulant",
        "clot activator reagent", "heparin", "edta", "clot activator", "silicone oil lubricant",
        "pdms medical fluid", "silicone oil", "pdms", "platinum-carbon (pt/c) slurry", "platinum-carbon slurry",
        "nafion ionomer suspension", "catalyst ink", "platinum", "pt/c", "carbon slurry", "nafion",
        "ito precursor solution", "zinc oxide (zno) solution", "ito", "zinc oxide", "zno", "tco",
        "cisplatin", "slurry", "aqueous coating solution", "aqueous solution", "aqueous", "solvent", "photoresist", "flux"
      ];
      for (var k = 0; k < knownMats.length; k++) {
        if (t.indexOf(knownMats[k]) !== -1) {
          state.material = knownMats[k].length <= 4 ? knownMats[k].toUpperCase() : knownMats[k].replace(/\b\w/g, function(l){ return l.toUpperCase(); });
          break;
        }
      }
      if (!state.material && expectedStep === "material" && !/price|cost|warranty|marathi|hindi|tamil|english/.test(t) && text.length > 1) {
        state.material = text;
      }

      // 3. Viscosity matching
      var viscMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:cp|centipoise|सेंटीपॉइज)/i) ||
                      text.match(/(?:viscosity|visc|व्हिस्कोसिटी|विस्कोसिटी)[^\d]{0,15}(\d+(?:\.\d+)?)/i);
      if (viscMatch) {
        state.viscosity_cp = parseFloat(viscMatch[1]);
      } else if (expectedStep === "viscosity") {
        var bareVisc = text.match(/^[^\d]*(\d+(?:\.\d+)?)[^\d]*$/);
        if (bareVisc) state.viscosity_cp = parseFloat(bareVisc[1]);
      }

      // 4. Flow rate / dispensing volume matching
      var flowMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:ml\s*\/\s*min|ml per min|ml\/m|ml\b|एमएल\/मिनिट|एमएल\/मिनट)/i) ||
                      text.match(/(?:flow rate|feed rate|flow|feed|फ्लो रेट|फीड रेट)[^\d]{0,15}(\d+(?:\.\d+)?)/i);
      if (flowMatch) {
        state.flow_rate_ml_min = parseFloat(flowMatch[1]);
      }

      var ulMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:ul|µl|microliter)/i);
      if (ulMatch) {
        state.dispensing_ul = parseFloat(ulMatch[1]);
        if (state.flow_rate_ml_min === null) {
          state.flow_rate_ml_min = parseFloat((parseFloat(ulMatch[1]) / 1000).toFixed(3));
        }
      }
      if (state.flow_rate_ml_min === null && expectedStep === "flow") {
        var bareFlow = text.match(/^[^\d]*(\d+(?:\.\d+)?)[^\d]*$/);
        if (bareFlow) state.flow_rate_ml_min = parseFloat(bareFlow[1]);
      }

      // 5. Droplet size matching
      var dropMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:um|µm|micron|microns|मायक्रॉन|माइक्रोन)/i) ||
                      text.match(/(?:droplet size|droplet|drop size|ड्रॉपलेट)[^\d]{0,15}(\d+(?:\.\d+)?)/i);
      if (dropMatch) {
        state.droplet_size_um = parseFloat(dropMatch[1]);
      } else if (expectedStep === "droplet") {
        var bareDrop = text.match(/^[^\d]*(\d+(?:\.\d+)?)[^\d]*$/);
        if (bareDrop) state.droplet_size_um = parseFloat(bareDrop[1]);
      }

      // Contact / Lead capture fields
      var emailMatch = text.match(/([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/);
      if (emailMatch) state.email = emailMatch[1];

      var phoneMatch = text.match(/((?:\+91[\-\s]?)?[6-9]\d{9}|\b\d{3}[\-\s]?\d{3}[\-\s]?\d{4}\b)/);
      if (phoneMatch) state.phone = phoneMatch[1].trim();

      var nameMatch = text.match(/(?:full name|my name is|i am|name)\s*[:\-]?\s*([A-Za-z\.\s]{2,35}?)(?:,|\n|\||company|email|phone|$)/i);
      if (nameMatch) state.client_name = nameMatch[1].trim();

      var compMatch = text.match(/(?:company name|company|organization)\s*[:\-]?\s*([A-Za-z0-9\s&\.\-]{2,45}?)(?:,|\n|\||email|phone|callback|preferred|$)/i);
      if (compMatch) state.company = compMatch[1].trim();

      var timeMatch = text.match(/(?:callback|follow-up|preferred date\s*(?:&\s*time)?|schedule|call slot)\s*[:\-]?\s*([^\n\|]{4,45})$/i) ||
                      text.match(/((?:monday|tuesday|wednesday|thursday|friday|saturday|tomorrow|oct|october|\d{1,2}[\/\-]\d{1,2}|\d{4}-\d{2}-\d{2})[^\.,;\n]{0,35}(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|ist|वाजता|बजे))?)/i);
      if (timeMatch && timeMatch[1].trim().length > 3) {
        state.callback_time = timeMatch[1].trim();
      }
    }

    var coreReady = (state.application || state.industry) &&
                    state.viscosity_cp !== null &&
                    (state.flow_rate_ml_min !== null || state.dispensing_ul !== null) &&
                    state.droplet_size_um !== null;
    if (coreReady) {
      var rec = recommendNozzle(state);
      state.recommended_product = rec.primary;
    }

    return state;
  }

  function recommendNozzle(state) {
    var visc = state.viscosity_cp;
    var flow = state.flow_rate_ml_min;
    var drop = state.droplet_size_um;
    var app = (state.application || "").toLowerCase();
    var ind = (state.industry || "").toLowerCase();

    if (visc !== null && visc > 1000) {
      return {
        primary: "High Viscosity, Conical (24 kHz or 60 kHz) - Engineering Evaluation Required",
        frequency: "24 kHz (60 µm) or 60 kHz (40 µm)",
        droplet: "40 µm to 60 µm",
        feed_rate: "Up to 3 ml/min",
        viscosity_limit: "< 1000 cP",
        accessories: [],
        reason_en: "Your fluid viscosity of " + visc + " cP exceeds the 1000 cP catalog maximum of our High Viscosity Conical nozzle. I will confirm this with the WaveNxD engineering team for custom slurry conditioning or testing."
      };
    }

    if (app.indexOf("stent") !== -1 || (drop !== null && drop <= 15)) {
      return {
        primary: "Standard Torch (180 kHz)",
        frequency: "180 kHz",
        droplet: "10 µm (Ultra-fine mist)",
        feed_rate: "5 ml/min",
        viscosity_limit: "< 50 cP",
        accessories: ["Micro Fluid Dispensing System (0 to 200 µl metered dispensing)"],
        reason_en: "The 180 kHz Standard Torch nozzle generates an ultra-fine 10 µm mist without hydraulic pressure, preventing polymer bridging across delicate stent struts at feed rates up to 5 ml/min and viscosities below 50 cP."
      };
    }

    if (app.indexOf("blood") !== -1 || app.indexOf("tube") !== -1) {
      return {
        primary: "Extended Horn, 15 mm (Conical, 60 kHz)",
        frequency: "60 kHz",
        droplet: "40 µm",
        feed_rate: "5 ml/min",
        viscosity_limit: "< 50 cP",
        accessories: ["Micro Fluid Dispensing System (0 to 200 µl metered dispensing)"],
        reason_en: "The 60 kHz Extended Horn (15 mm conical) nozzle reaches inside blood collection tubes to deposit a uniform 40 µm coating at up to 5 ml/min for fluids under 50 cP."
      };
    }

    if (app.indexOf("syringe") !== -1) {
      return {
        primary: "Extended Horn, 25 mm (Torch, 60 kHz)",
        frequency: "60 kHz",
        droplet: "40 µm",
        feed_rate: "5 ml/min",
        viscosity_limit: "< 1000 cP",
        accessories: ["Micro Fluid Dispensing System (0 to 200 µl metered dispensing)"],
        reason_en: "The 60 kHz Extended Horn (25 mm torch) nozzle is designed for narrow-bore syringe barrel coating and handles viscosities up to 1000 cP with a 40 µm droplet size and 5 ml/min feed rate."
      };
    }

    if (app.indexOf("pipac") !== -1 || app.indexOf("chemotherapy") !== -1) {
      return {
        primary: "PIPAC, Conical (60 kHz)",
        frequency: "60 kHz",
        droplet: "40 µm",
        feed_rate: "20 ml/min",
        viscosity_limit: "50 cP",
        accessories: [],
        reason_en: "The 60 kHz PIPAC Conical nozzle is specifically engineered for PIPAC chemotherapy applications, delivering 40 µm droplets at a 20 ml/min feed rate up to 50 cP."
      };
    }

    if (app.indexOf("tco") !== -1 || app.indexOf("micro-coating") !== -1 || (app.indexOf("pyrolysis") !== -1 && (ind.indexOf("electronics") !== -1 || ind.indexOf("semiconductor") !== -1))) {
      return {
        primary: "PLC-Controlled XY Spray Pyrolysis System with Standard Nozzle (60 kHz / 120 kHz)",
        frequency: "60 kHz (40 µm) or 120 kHz (25 µm)",
        droplet: "25 µm to 40 µm",
        feed_rate: "3 to 5 ml/min",
        viscosity_limit: "< 50 cP",
        accessories: ["Air-Shaping Attachments (focused beam or wide spray dispersion)"],
        reason_en: "For transparent conductive oxide (TCO) and micro-coating applications, our PLC-Controlled XY Spray Pyrolysis System provides an SS316 enclosure and substrate heating up to 450°C paired with our Standard nozzle family."
      };
    }

    if ((visc !== null && visc > 50) || app.indexOf("fuel cell") !== -1) {
      var is24 = drop !== null && drop >= 50;
      return {
        primary: is24 ? "High Viscosity, Conical (24 kHz)" : "High Viscosity, Conical (60 kHz)",
        frequency: is24 ? "24 kHz" : "60 kHz (also available in 24 kHz for 60 µm droplets)",
        droplet: is24 ? "60 µm" : "40 µm",
        feed_rate: "Up to 3 ml/min",
        viscosity_limit: "< 1000 cP",
        accessories: ["Air-Shaping Attachments (focused beam or wide spray dispersion)"],
        reason_en: "For fuel cell catalyst slurries and viscous fluids up to 1000 cP, the High Viscosity Conical nozzle atomizes dense slurries without clogging at feed rates up to 3 ml/min."
      };
    }

    if ((flow !== null && flow > 20) || app.indexOf("industrial spray") !== -1) {
      return {
        primary: "High Flow, Conical (60 kHz)",
        frequency: "60 kHz",
        droplet: "40 µm",
        feed_rate: "Up to 200 ml/min",
        viscosity_limit: "< 50 cP",
        accessories: [],
        reason_en: "The 60 kHz High Flow Conical nozzle supports feed rates up to 200 ml/min with 40 µm droplets for industrial spray drying of fluids below 50 cP."
      };
    }

    if (app.indexOf("powder") !== -1 || app.indexOf("hydrogen") !== -1 || (drop !== null && drop >= 16 && drop <= 30)) {
      return {
        primary: "Standard Family - 120 kHz (torch, conical, flat; dual-feed flat oval)",
        frequency: "120 kHz",
        droplet: "25 µm",
        feed_rate: "3 ml/min",
        viscosity_limit: "< 50 cP",
        accessories: [],
        reason_en: "The 120 kHz Standard Family nozzle delivers uniform 25 µm droplets at up to 3 ml/min (< 50 cP), ideal for powder synthesis, hydrogen production, and spray pyrolysis."
      };
    }

    return {
      primary: "Standard Family - 60 kHz (torch, conical, flat)",
      frequency: "60 kHz",
      droplet: "40 µm",
      feed_rate: "5 ml/min",
      viscosity_limit: "< 50 cP",
      accessories: [],
      reason_en: "The 60 kHz Standard Family nozzle produces uniform 40 µm droplets at up to 5 ml/min for fluids under 50 cP, suited for lab spray drying and spray pyrolysis."
    };
  }

  function getMaterialOptionsForApp(appStr) {
    var a = (appStr || "").toLowerCase();
    if (a.indexOf("stent") !== -1) {
      return ["PLGA Drug-Polymer Solution", "Sirolimus Polymer Coating", "PDLLA Solution", "Aqueous Solution"];
    }
    if (a.indexOf("syringe") !== -1) {
      return ["Silicone Oil Lubricant", "PDMS Medical Fluid", "Aqueous Coating Solution"];
    }
    if (a.indexOf("blood") !== -1 || a.indexOf("tube") !== -1) {
      return ["EDTA Anticoagulant", "Heparin Solution", "Clot Activator Reagent"];
    }
    if (a.indexOf("fuel cell") !== -1 || a.indexOf("hydrogen") !== -1) {
      return ["Platinum-Carbon (Pt/C) Slurry", "Nafion Ionomer Suspension", "Catalyst Ink"];
    }
    if (a.indexOf("tco") !== -1 || a.indexOf("pyrolysis") !== -1) {
      return ["ITO Precursor Solution", "Zinc Oxide (ZnO) Solution", "Aqueous Precursor"];
    }
    return [
      "PLGA Drug-Polymer Solution",
      "Platinum-Carbon Slurry",
      "Silicone Oil Lubricant",
      "Aqueous Solution",
      "ITO Precursor Solution"
    ];
  }

  function buildNextStepReply(msgList) {
    var state = extractState(msgList);
    var lang = state.language;
    var lastUser = "";
    for (var i = msgList.length - 1; i >= 0; i--) {
      if (msgList[i].role === "user") {
        lastUser = msgList[i].content.trim();
        break;
      }
    }
    var t = lastUser.toLowerCase();

    if (/weather|cricket|movie|recipe|politics|bitcoin|joke|football/.test(t)) {
      return {
        reply: "I specialize in ultrasonic spray nozzle systems at WaveNxD Technologies, Kolhapur. Let us continue finding the right nozzle for your application.",
        options: INITIAL_OPTIONS_EN,
        showLeadForm: false,
        state: state
      };
    }

    var notes = [];
    if (/price|cost|pricing|how much|किंमत|कीमत|விலை/.test(t)) {
      if (lang === "mr") {
        notes.push("किंमत (Pricing) ही तुमच्या संपूर्ण सिस्टीम इंटिग्रेशन, जनरेटर आणि माउंटिंग सेटअपवर अवलंबून असते. आमची सेल्स इंजिनिअरिंग टीम तुमच्या अधिकृत कोटेशनमध्ये संपूर्ण किंमत समाविष्ट करेल.");
      } else if (lang === "hi") {
        notes.push("प्राइसिंग (Pricing) आपके सिस्टम इंटीग्रेशन, जनरेटर और माउंटिंग सेटअप पर निर्भर करती है। हमारी सेल्स इंजीनियरिंग टीम आपके आधिकारिक कोटेशन में पूरी कीमत शामिल करेगी।");
      } else {
        notes.push("Pricing depends on the exact system integration, generator, and mounting setup. I will have our sales engineering team include full pricing in your quotation.");
      }
    }
    if (/warranty|delivery time|lead time|watt|voltage|dimension|weight|वॉरंटी|डिलिव्हरी|डिलीवरी/.test(t)) {
      notes.push("Regarding that specific detail: I will confirm this with the WaveNxD engineering team.");
    }
    if (/model number|part number/.test(t)) {
      notes.push("Catalog model numbers are unassigned; we identify and recommend systems strictly by operating frequency, nozzle family/type, and primary application.");
    }
    var prefix = notes.length > 0 ? notes.join("\n\n") + "\n\n" : "";

    // ONE-BY-ONE CONVERSATIONAL QUESTION FLOW WITH OPTIONS
    // Question 1: Industry & Application
    if (!state.application && !state.industry) {
      if (lang === "mr") {
        return {
          reply: prefix + "नमस्कार, मी अर्जुन कुलकर्णी, WaveNxD Technologies Pvt. Ltd., कोल्हापूर येथून बोलत आहे. आमचे नो-प्रेशर अल्ट्रासोनिक स्प्रे नोझल बिना प्रेशरच्या मऊ आणि एकसमान droplets तयार करतात.\n\nसुरुवातीला, तुम्ही कोणत्या इंडस्ट्री आणि कोटिंग अ‍ॅप्लिकेशनसाठी (Application) नोझल शोधत आहात? खालीलपैकी एक पर्याय निवडा किंवा टाइप करा:",
          options: [
            "Medical Devices - Stent Coating",
            "Medical Devices - Syringe Coating",
            "Medical Devices - Blood Collection Tubes",
            "Energy - Fuel Cell Coating",
            "Pharma - Lab Spray Dryer",
            "Industrial Spray Dryer (High Flow)",
            "Electronics - TCO / Spray Pyrolysis"
          ],
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "hi") {
        return {
          reply: prefix + "नमस्ते, मैं अर्जुन कुलकर्णी, WaveNxD Technologies Pvt. Ltd., कोल्हापुर से हूँ। हमारे अल्ट्रासोनिक नोजल बिना किसी हाइड्रोलिक प्रेशर के अत्यंत महीन और एकसमान droplets बनाते हैं।\n\nशुरू करने के लिए, आप किस इंडस्ट्री और एप्लिकेशन (Application) के लिए नोजल देख रहे हैं? नीचे से एक विकल्प चुनें या टाइप करें:",
          options: [
            "Medical Devices - Stent Coating",
            "Medical Devices - Syringe Coating",
            "Medical Devices - Blood Collection Tubes",
            "Energy - Fuel Cell Coating",
            "Pharma - Lab Spray Dryer",
            "Industrial Spray Dryer (High Flow)",
            "Electronics - TCO / Spray Pyrolysis"
          ],
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "ta") {
        return {
          reply: prefix + "வணக்கம், நான் அர்ஜுன் குல்கர்னி, WaveNxD Technologies Pvt. Ltd., கோலாப்பூர். எங்கள் அல்ட்ராசோனிக் நாசில்கள் அழுத்தம் இல்லாமல் சீரான நுண் துளிகளை (fine droplets) உருவாக்குகின்றன.\n\nமுதலில், உங்கள் துறை மற்றும் பயன்பாட்டை (Application) கீழே உள்ள விருப்பங்களில் இருந்து தேர்ந்தெடுக்கவும்:",
          options: [
            "Medical Devices - Stent Coating",
            "Medical Devices - Syringe Coating",
            "Energy - Fuel Cell Coating",
            "Pharma - Lab Spray Dryer",
            "Electronics - TCO / Spray Pyrolysis"
          ],
          showLeadForm: false,
          state: state
        };
      }
      return {
        reply: prefix + "Which target industry and specific coating or spray application are you working on? Please pick one of the options below or type your own:",
        options: INITIAL_OPTIONS_EN,
        showLeadForm: false,
        state: state
      };
    }

    // Question 2: Liquid / Coating Material
    if (!state.material) {
      var matOptions = getMaterialOptionsForApp(state.application || state.industry);
      if (lang === "mr") {
        return {
          reply: prefix + "छान, आम्ही " + (state.application || state.industry) + " साठी काम करतो. या प्रक्रियेत तुम्ही कोणते लिक्विड किंवा कोटिंग मटेरियल (Material) स्प्रे करणार आहात?",
          options: matOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "hi") {
        return {
          reply: prefix + "बहुत बढ़िया, " + (state.application || state.industry) + " के लिए हमारे पास विशेष समाधान हैं। आप इसमें कौन सा लिक्विड या कोटिंग मटेरियल (Material) स्प्रे करेंगे?",
          options: matOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "ta") {
        return {
          reply: prefix + "நல்லது (" + (state.application || state.industry) + "). இதில் நீங்கள் பயன்படுத்தும் திரவம் (Liquid / Coating Material) என்ன?",
          options: matOptions,
          showLeadForm: false,
          state: state
        };
      }
      return {
        reply: prefix + "Got it — " + (state.application || state.industry) + " is a core application for WaveNxD. What liquid, coating solution, or slurry material will you be spraying?",
        options: matOptions,
        showLeadForm: false,
        state: state
      };
    }

    // Question 3: Viscosity (in cP)
    if (state.viscosity_cp === null) {
      var viscOptions = [
        "12 cP (Low viscosity, < 50 cP)",
        "35 cP (Standard viscosity, < 50 cP)",
        "350 cP (Medium-high viscosity, < 1000 cP)",
        "650 cP (Thick slurry, < 1000 cP)",
        "1200 cP (Above 1000 cP)"
      ];
      if (lang === "mr") {
        return {
          reply: prefix + "समजले (" + state.material + "). तुमच्या लिक्विडची viscosity (cP मध्ये) किती आहे? खालीलपैकी एक पर्याय निवडा किंवा आकडा टाइप करा:",
          options: viscOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "hi") {
        return {
          reply: prefix + "समझ गया (" + state.material + ")। आपके लिक्विड की viscosity (cP में) कितनी है? नीचे से चुनें या टाइप करें:",
          options: viscOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "ta") {
        return {
          reply: prefix + "புரிந்தது (" + state.material + "). உங்கள் திரவத்தின் viscosity (cP-ல்) எவ்வளவு?",
          options: viscOptions,
          showLeadForm: false,
          state: state
        };
      }
      return {
        reply: prefix + "Understood, you are spraying " + state.material + ". What is the approximate liquid viscosity (in cP)?",
        options: viscOptions,
        showLeadForm: false,
        state: state
      };
    }

    // Question 4: Required Flow / Feed Rate (in ml/min or µl)
    if (state.flow_rate_ml_min === null && state.dispensing_ul === null) {
      var flowOptions = [
        "2 ml/min (Up to 3 ml/min)",
        "5 ml/min (Standard feed rate)",
        "20 ml/min (PIPAC feed rate)",
        "150 ml/min (High flow up to 200 ml/min)",
        "100 µl (Metered micro-dispensing 0-200 µl)"
      ];
      if (lang === "mr") {
        return {
          reply: prefix + "धन्यवाद (Viscosity: " + state.viscosity_cp + " cP). आता कृपया तुम्हाला आवश्यक असलेला flow rate / feed rate (ml/min किंवा µl मध्ये) निवडा:",
          options: flowOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "hi") {
        return {
          reply: prefix + "धन्यवाद (Viscosity: " + state.viscosity_cp + " cP)। अब कृपया अपनी आवश्यक flow rate / feed rate (ml/min या µl में) चुनें:",
          options: flowOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "ta") {
        return {
          reply: prefix + "நன்றி (Viscosity: " + state.viscosity_cp + " cP). உங்களுக்குத் தேவையான flow rate (ml/min அல்லது µl-ல்) எவ்வளவு?",
          options: flowOptions,
          showLeadForm: false,
          state: state
        };
      }
      return {
        reply: prefix + "Noted (" + state.viscosity_cp + " cP viscosity). What required flow rate (in ml/min) or metered dispensing volume (in µl) does your process need?",
        options: flowOptions,
        showLeadForm: false,
        state: state
      };
    }

    // Question 5: Target Droplet Size (in µm)
    if (state.droplet_size_um === null) {
      var dropOptions = [
        "10 µm (Ultra-fine mist - 180 kHz)",
        "25 µm (Fine mist - 120 kHz)",
        "40 µm (Standard mist - 60 kHz)",
        "60 µm (Viscous slurry mist - 24 kHz)"
      ];
      if (lang === "mr") {
        return {
          reply: prefix + "छान (Flow rate: " + state.flow_rate_ml_min + " ml/min). शेवटचा प्रश्न: तुमच्या कोटिंगसाठी आवश्यक droplet size (µm मध्ये) किती हवा आहे?",
          options: dropOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "hi") {
        return {
          reply: prefix + "बहुत अच्छे (Flow rate: " + state.flow_rate_ml_min + " ml/min)। अंतिम प्रश्न: आपकी कोटिंग के लिए टारगेट droplet size (µm में) क्या होनी चाहिए?",
          options: dropOptions,
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "ta") {
        return {
          reply: prefix + "நன்றி (Flow rate: " + state.flow_rate_ml_min + " ml/min). கடைசியாக, உங்களுக்குத் தேவையான droplet size (µm-ல்) என்ன?",
          options: dropOptions,
          showLeadForm: false,
          state: state
        };
      }
      return {
        reply: prefix + "Great (" + state.flow_rate_ml_min + " ml/min flow rate). Finally, what is your target droplet size (in µm)?",
        options: dropOptions,
        showLeadForm: false,
        state: state
      };
    }

    // All 5 technical parameters are complete!
    var rec = recommendNozzle(state);
    state.recommended_product = rec.primary;

    var leadComplete = state.client_name && state.company && state.email && state.phone && state.callback_time;

    // Step 7: Final Confirmation Summary after the client submits the form
    if (leadComplete) {
      var accLine = rec.accessories.length ? "\n- Companion System / Accessory: " + rec.accessories.join("; ") : "";
      if (lang === "mr") {
        return {
          reply: "धन्यवाद! तुमच्या सर्व आवश्यकता आणि संपर्काचे तपशील निश्चित झाले आहेत. खाली संपूर्ण सारांश दिला आहे:\n\n" +
                 "1. ग्राहकांच्या गरजा (Client Requirement Summary):\n" +
                 "- Industry & Application: " + (state.industry || "Specified") + " (" + (state.application || "Coating") + ")\n" +
                 "- Liquid / Material: " + (state.material || "Specified fluid") + "\n" +
                 "- Viscosity: " + state.viscosity_cp + " cP | Flow Rate: " + state.flow_rate_ml_min + " ml/min | Droplet Size: " + state.droplet_size_um + " µm\n\n" +
                 "2. शिफारस केलेली प्रणाली (Recommended WaveNxD System):\n" +
                 "- System Family: " + rec.primary + "\n" +
                 "- Frequency: " + rec.frequency + " | Droplet Size: " + rec.droplet + "\n" +
                 "- Feed Rate: " + rec.feed_rate + " | Viscosity Limit: " + rec.viscosity_limit + accLine + "\n\n" +
                 "3. कोटेशन आणि फॉलो-अप कॉल (Quotation & Follow-Up Schedule):\n" +
                 "- Full Name: " + state.client_name + "\n" +
                 "- Company Name: " + state.company + "\n" +
                 "- Email Address: " + state.email + " (फॉलो-अपसाठी नोंदवले आहे)\n" +
                 "- Phone Number: " + state.phone + "\n" +
                 "- Scheduled Follow-Up Call: " + state.callback_time,
          options: ["What is the price?", "What is the warranty?", "Start a new inquiry"],
          showLeadForm: false,
          state: state
        };
      }
      if (lang === "hi") {
        return {
          reply: "धन्यवाद! आपकी सभी आवश्यकताएं और संपर्क विवरण दर्ज कर लिए गए हैं। पूरा सारांश नीचे दिया गया है:\n\n" +
                 "1. तकनीकी आवश्यकताएं (Client Requirement Summary):\n" +
                 "- Industry & Application: " + (state.industry || "Specified") + " (" + (state.application || "Coating") + ")\n" +
                 "- Liquid / Material: " + (state.material || "Specified fluid") + "\n" +
                 "- Viscosity: " + state.viscosity_cp + " cP | Flow Rate: " + state.flow_rate_ml_min + " ml/min | Droplet Size: " + state.droplet_size_um + " µm\n\n" +
                 "2. अनुशंसित सिस्टम (Recommended WaveNxD System):\n" +
                 "- System Family: " + rec.primary + "\n" +
                 "- Frequency: " + rec.frequency + " | Droplet Size: " + rec.droplet + "\n" +
                 "- Feed Rate: " + rec.feed_rate + " | Viscosity Limit: " + rec.viscosity_limit + accLine + "\n\n" +
                 "3. कोटेशन और फॉलो-अप कॉल (Quotation & Follow-Up Schedule):\n" +
                 "- Full Name: " + state.client_name + "\n" +
                 "- Company Name: " + state.company + "\n" +
                 "- Email Address: " + state.email + " (फॉलो-अप के लिए दर्ज किया गया)\n" +
                 "- Phone Number: " + state.phone + "\n" +
                 "- Scheduled Follow-Up Call: " + state.callback_time,
          options: ["What is the price?", "What is the warranty?", "Start a new inquiry"],
          showLeadForm: false,
          state: state
        };
      }
      return {
        reply: "Thank you. Your technical requirements and contact details have been finalized. Here is your complete confirmation summary:\n\n" +
               "1. Client Requirement Parameters:\n" +
               "- Industry & Application: " + (state.industry || "Specified") + " (" + (state.application || "Coating") + ")\n" +
               "- Liquid / Coating Material: " + (state.material || "Process Fluid") + "\n" +
               "- Liquid Viscosity: " + state.viscosity_cp + " cP\n" +
               "- Required Flow / Feed Rate: " + state.flow_rate_ml_min + " ml/min\n" +
               "- Target Droplet Size: " + state.droplet_size_um + " µm\n\n" +
               "2. Recommended WaveNxD Nozzle System:\n" +
               "- System Family: " + rec.primary + "\n" +
               "- Operating Frequency: " + rec.frequency + " | Droplet Size: " + rec.droplet + "\n" +
               "- Feed Rate Capacity: " + rec.feed_rate + " | Viscosity Limit: " + rec.viscosity_limit + accLine + "\n" +
               "- Engineering Fit: " + rec.reason_en + "\n\n" +
               "3. Quotation Dispatch & Scheduled Callback:\n" +
               "- Full Name: " + state.client_name + "\n" +
               "- Company Name: " + state.company + "\n" +
               "- Email Address: " + state.email + " (Contact for follow-up)\n" +
               "- Phone Number: " + state.phone + "\n" +
               "- Scheduled Follow-Up Call: " + state.callback_time + "\n\n" +
               "Our WaveNxD engineering team in Kolhapur has received your request and will email the formal quotation and connect with you at the scheduled time.",
        options: ["What is the price?", "What is the delivery lead time?", "Start a new inquiry"],
        showLeadForm: false,
        state: state
      };
    }

    // Step 5 & 6: Recommendation + Show Inline Lead Capture Form
    var accNote = rec.accessories.length ? "\n- Companion System / Accessory: " + rec.accessories.join("; ") : "";
    if (lang === "mr") {
      return {
        reply: prefix +
               "तुमच्या सर्व आवश्यकतांनुसार (" + (state.application || state.industry) + ", मटेरियल " + state.material + ", viscosity " + state.viscosity_cp + " cP, flow rate " + state.flow_rate_ml_min + " ml/min, आणि droplet size " + state.droplet_size_um + " µm), मी WaveNxD कॅटलॉगमधील खालील प्रणाली सुचवतो:\n\n" +
               "शिफारस केलेली प्रणाली: " + rec.primary + "\n" +
               "- Operating Frequency: " + rec.frequency + "\n" +
               "- Catalog Droplet Size: " + rec.droplet + "\n" +
               "- Feed Rate Capacity: " + rec.feed_rate + "\n" +
               "- Viscosity Limit: " + rec.viscosity_limit + accNote + "\n\n" +
               "तांत्रिक कारण: हे नोझल बिना प्रेशरच्या एकसमान " + rec.droplet + " droplets तयार करते आणि तुमच्या " + state.viscosity_cp + " cP viscosity व " + state.flow_rate_ml_min + " ml/min flow rate ला तंतोतंत जुळते.\n\n" +
               "WaveNxD टीमकडे कोटेशनची विनंती पाठवण्यासाठी आणि टेक्निकल फॉलो-अप कॉल निश्चित करण्यासाठी कृपया खालील फॉर्ममध्ये तुमचे तपशील भरा. टीम अधिकृत कोटेशन ईमेलद्वारे पाठवेल:",
        options: ["किंमत काय आहे? (What is the price?)", "वॉरंटी आणि डिलिव्हरी वेळ काय आहे?"],
        showLeadForm: true,
        state: state
      };
    }
    if (lang === "hi") {
      return {
        reply: prefix +
               "आपकी आवश्यकताओं (" + (state.application || state.industry) + ", मटेरियल " + state.material + ", viscosity " + state.viscosity_cp + " cP, flow rate " + state.flow_rate_ml_min + " ml/min, और droplet size " + state.droplet_size_um + " µm) के अनुसार, मैं WaveNxD कैटलॉग से निम्नलिखित सिस्टम की सिफारिश करता हूँ:\n\n" +
               "अनुशंसित सिस्टम: " + rec.primary + "\n" +
               "- Operating Frequency: " + rec.frequency + "\n" +
               "- Catalog Droplet Size: " + rec.droplet + "\n" +
               "- Feed Rate Capacity: " + rec.feed_rate + "\n" +
               "- Viscosity Limit: " + rec.viscosity_limit + accNote + "\n\n" +
               "तकनीकी कारण: यह नोजल बिना किसी हाइड्रोलिक प्रेशर के " + rec.droplet + " के एकसमान droplets बनाता है और आपकी " + state.viscosity_cp + " cP viscosity तथा " + state.flow_rate_ml_min + " ml/min flow rate के पूरी तरह अनुकूल है।\n\n" +
               "WaveNxD टीम को कोटेशन अनुरोध भेजने और टेक्निकल फॉलो-अप कॉल तय करने के लिए नीचे दिया गया फॉर्म भरें। टीम आधिकारिक कोटेशन ईमेल से भेजेगी:",
        options: ["इसकी कीमत क्या है? (What is the price?)", "वारंटी और डिलीवरी का समय क्या है?"],
        showLeadForm: true,
        state: state
      };
    }

    return {
      reply: prefix +
             "Based on all of your parameters (" + (state.application || state.industry) + ", spraying " + state.material + " at " + state.viscosity_cp + " cP viscosity, " + state.flow_rate_ml_min + " ml/min flow rate, and " + state.droplet_size_um + " µm droplet size), here is the best match from the WaveNxD catalog:\n\n" +
             "Recommended System: " + rec.primary + "\n" +
             "- Operating Frequency: " + rec.frequency + "\n" +
             "- Catalog Droplet Size: " + rec.droplet + "\n" +
             "- Feed Rate Capacity: " + rec.feed_rate + "\n" +
             "- Viscosity Limit: " + rec.viscosity_limit + accNote + "\n\n" +
             "Why this fits your application: " + rec.reason_en + "\n\n" +
             "To send a quotation request to our team and schedule a technical follow-up call, please fill in the form below. Our team will send the formal quotation by email:",
      options: ["What is the price of this system?", "What is the delivery lead time?"],
      showLeadForm: true,
      state: state
    };
  }

  function updateSidebarProgress(state) {
    lastState = state;
    function updateStep(stepId, valId, val) {
      var stepEl = document.getElementById(stepId);
      var valEl = document.getElementById(valId);
      if (!stepEl || !valEl) return;
      if (val) {
        stepEl.className = "progress-step done";
        valEl.textContent = val;
      } else {
        stepEl.className = "progress-step";
        valEl.textContent = "Pending";
      }
    }
    updateStep("stepApp", "valApp", state.application || state.industry);
    updateStep("stepMat", "valMat", state.material);
    updateStep("stepVisc", "valVisc", state.viscosity_cp !== null ? state.viscosity_cp + " cP" : null);
    updateStep("stepFlow", "valFlow", state.flow_rate_ml_min !== null ? state.flow_rate_ml_min + " ml/min" : null);
    updateStep("stepDrop", "valDrop", state.droplet_size_um !== null ? state.droplet_size_um + " µm" : null);
    updateStep("stepRec", "valRec", state.recommended_product);
    var leadDone = (state.client_name && state.email && state.callback_time)
      ? state.client_name + " (" + state.callback_time + ")"
      : null;
    updateStep("stepLead", "valLead", leadDone);
  }

  function createLeadFormElement() {
    var card = document.createElement("div");
    card.className = "lead-form-card";

    var title = document.createElement("div");
    title.className = "lead-form-title";
    title.textContent = "Quotation Request & Follow-Up Call Booking";
    card.appendChild(title);

    var sub = document.createElement("div");
    sub.className = "lead-form-subtitle";
    sub.textContent = "Enter your details to send a quotation request to WaveNxD and confirm a callback slot. Our team will follow up by email.";
    card.appendChild(sub);

    var grid = document.createElement("div");
    grid.className = "lead-form-grid";

    function makeField(labelTxt, placeholderTxt, typeTxt, fullWidth) {
      var wrap = document.createElement("div");
      wrap.className = fullWidth ? "lead-form-field full-width" : "lead-form-field";
      var lbl = document.createElement("label");
      lbl.textContent = labelTxt;
      var inp = document.createElement("input");
      inp.type = typeTxt || "text";
      inp.placeholder = placeholderTxt;
      wrap.appendChild(lbl);
      wrap.appendChild(inp);
      grid.appendChild(wrap);
      return inp;
    }

    var inpName = makeField("Full Name *", "e.g., Dr. Rohan Mehta", "text", false);
    var inpCompany = makeField("Company Name *", "e.g., Mehta MedTech Pvt. Ltd.", "text", false);
    var inpEmail = makeField("Email Address *", "e.g., rohan@mehtamedtech.in", "email", false);
    var inpPhone = makeField("Phone Number *", "e.g., 9876543210", "tel", false);
    var inpTime = makeField("Preferred Date & Time for Follow-Up Call *", "e.g., Friday 24 Oct at 11:00 AM", "text", true);

    card.appendChild(grid);

    var errLine = document.createElement("div");
    errLine.style.color = "#f87171";
    errLine.style.fontSize = "12px";
    errLine.style.marginBottom = "8px";
    errLine.style.display = "none";
    card.appendChild(errLine);

    var actions = document.createElement("div");
    actions.className = "lead-form-actions";

    var btnSample = document.createElement("button");
    btnSample.type = "button";
    btnSample.className = "btn-secondary";
    btnSample.textContent = "Fill Sample Details";
    btnSample.addEventListener("click", function () {
      inpName.value = "Dr. Rohan Mehta";
      inpCompany.value = "Mehta MedTech Pvt. Ltd.";
      inpEmail.value = "rohan@mehtamedtech.in";
      inpPhone.value = "9876543210";
      inpTime.value = "Friday 24 Oct at 11:00 AM";
      errLine.style.display = "none";
    });

    var btnSubmit = document.createElement("button");
    btnSubmit.type = "button";
    btnSubmit.className = "send-btn";
    btnSubmit.textContent = "Confirm & Finalize Details";
    btnSubmit.addEventListener("click", function () {
      var nm = inpName.value.trim();
      var cp = inpCompany.value.trim();
      var em = inpEmail.value.trim();
      var ph = inpPhone.value.trim();
      var tm = inpTime.value.trim();
      if (!nm || !cp || !em || !ph || !tm) {
        errLine.textContent = "Please fill in all 5 fields (or click 'Fill Sample Details') to finalize your booking.";
        errLine.style.display = "block";
        return;
      }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em)) {
        errLine.textContent = "Please enter a valid email address.";
        errLine.style.display = "block";
        return;
      }
      var phoneDigits = ph.replace(/\D/g, "");
      if (phoneDigits.length < 7 || phoneDigits.length > 15) {
        errLine.textContent = "Please enter a valid phone number.";
        errLine.style.display = "block";
        return;
      }
      btnSubmit.disabled = true;
      btnSample.disabled = true;
      var formattedMsg =
        "Full Name: " + nm +
        " | Company Name: " + cp +
        " | Email: " + em +
        " | Phone: " + ph +
        " | Preferred Date & Time: " + tm;
      var conversation = messages.map(function (message) {
        return message.role + ": " + message.content;
      }).join("\n\n");
      btnSubmit.textContent = "Sending...";
      errLine.style.display = "none";

      fetch("/api/send_enquiry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_name: nm,
          company: cp,
          email: em,
          phone: ph,
          callback_slot: tm,
          conversation: conversation
        })
      }).then(function (response) {
        return response.text().then(function (body) {
          var result;
          try {
            result = JSON.parse(body);
          } catch (parseError) {
            if (response.status === 404) {
              throw new Error("This server does not have the enquiry endpoint. Stop it and restart app.py from the SalesGPT project folder.");
            }
            throw new Error("The server returned an unexpected response (HTTP " + response.status + "). Please try again.");
          }
          if (!response.ok || result.status !== "success") {
            throw new Error(result.message || "The enquiry email could not be sent.");
          }
          return result;
        });
      }).then(function () {
        btnSubmit.textContent = "Submitted";
        sendUserMessage(formattedMsg);
      }).catch(function (error) {
        errLine.textContent = error.message || "The enquiry email could not be sent. Please try again.";
        errLine.style.display = "block";
        btnSubmit.disabled = false;
        btnSample.disabled = false;
        btnSubmit.textContent = "Confirm & Finalize Details";
      });
    });

    actions.appendChild(btnSample);
    actions.appendChild(btnSubmit);
    card.appendChild(actions);

    return card;
  }

  function appendMessageUI(role, content, optionsList, showLeadForm) {
    var row = document.createElement("div");
    row.className = "message-row " + role;

    var roleLabel = document.createElement("div");
    roleLabel.className = "message-role";
    roleLabel.textContent = role === "user" ? "Client" : "Arjun Kulkarni (WaveNxD Sales Engineer)";

    var bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = content;

    row.appendChild(roleLabel);
    row.appendChild(bubble);

    if (role === "assistant" && showLeadForm) {
      row.appendChild(createLeadFormElement());
    }

    if (role === "assistant" && optionsList && optionsList.length > 0) {
      var optContainer = document.createElement("div");
      optContainer.className = "options-container";
      for (var i = 0; i < optionsList.length; i++) {
        (function (optText) {
          var chip = document.createElement("button");
          chip.type = "button";
          chip.className = "option-chip";
          chip.textContent = optText;
          chip.addEventListener("click", function () {
            if (optText === "Start a new inquiry") {
              resetChat();
              return;
            }
            sendUserMessage(optText);
          });
          optContainer.appendChild(chip);
        })(optionsList[i]);
      }
      row.appendChild(optContainer);
    }

    chatStream.appendChild(row);
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  function speakText(text, langCode) {
    if (!ttsEnabled || !("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel();
      var utter = new SpeechSynthesisUtterance(text);
      if (langCode === "mr") utter.lang = "mr-IN";
      else if (langCode === "hi") utter.lang = "hi-IN";
      else if (langCode === "ta") utter.lang = "ta-IN";
      else utter.lang = voiceLangSelect.value || "en-IN";
      window.speechSynthesis.speak(utter);
    } catch (e) {}
  }

  function sendUserMessage(text) {
    if (!text || !text.trim()) return;
    var cleanText = text.trim();
    messages.push({ role: "user", content: cleanText });
    appendMessageUI("user", cleanText, null, false);
    userInput.value = "";

    var result = buildNextStepReply(messages);
    messages.push({ role: "assistant", content: result.reply });
    appendMessageUI("assistant", result.reply, result.options, result.showLeadForm);
    updateSidebarProgress(result.state);
    speakText(result.reply, result.state.language);
  }

  function resetChat() {
    messages = [{ role: "assistant", content: INITIAL_GREETING }];
    chatStream.innerHTML = "";
    appendMessageUI("assistant", INITIAL_GREETING, INITIAL_OPTIONS_EN, false);
    updateSidebarProgress({
      language: "en",
      application: null,
      industry: null,
      material: null,
      viscosity_cp: null,
      flow_rate_ml_min: null,
      droplet_size_um: null,
      recommended_product: null,
      client_name: null,
      email: null,
      callback_time: null
    });
  }

  chatForm.addEventListener("submit", function (e) {
    e.preventDefault();
    sendUserMessage(userInput.value);
  });

  userInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendUserMessage(userInput.value);
    }
  });

  btnNewChat.addEventListener("click", function () {
    resetChat();
  });

  voiceLangSelect.addEventListener("change", function () {
    var val = voiceLangSelect.value;
    if (val === "mr-IN") {
      sendUserMessage("मराठीत बोला (Switch to Marathi)");
    } else if (val === "hi-IN") {
      sendUserMessage("हिंदी में बात करें (Switch to Hindi)");
    } else if (val === "ta-IN") {
      sendUserMessage("தமிழில் பேசவும் (Switch to Tamil)");
    } else {
      sendUserMessage("Switch to English");
    }
  });

  btnToggleTTS.addEventListener("click", function () {
    ttsEnabled = !ttsEnabled;
    btnToggleTTS.textContent = ttsEnabled ? "Voice Output: On" : "Voice Output: Off";
    btnToggleTTS.className = ttsEnabled ? "control-btn active" : "control-btn";
    if (!ttsEnabled && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  });

  function stopMicUI() {
    isRecording = false;
    btnMic.textContent = "Speak";
    btnMic.className = "icon-btn";
    micStatusBanner.className = "mic-status-banner";
  }

  function showVoiceFallbackHelper(reasonMsg) {
    micStatusBanner.className = "mic-status-banner visible";
    var step = getLastBotQuestionStep(lastState || {});
    var sampleVoiceText = "Medical Devices - Stent Coating";
    if (step === "material") sampleVoiceText = "PLGA Drug-Polymer Solution";
    else if (step === "viscosity") sampleVoiceText = "12 cP";
    else if (step === "flow") sampleVoiceText = "2 ml/min";
    else if (step === "droplet") sampleVoiceText = "10 µm";
    else if (step === "lead") sampleVoiceText = "Full Name: Dr. Rohan Mehta | Company Name: Mehta MedTech | Email: rohan@mehtamedtech.in | Phone: 9876543210 | Preferred Date & Time: Friday 11 AM";

    micStatusText.textContent = reasonMsg + " Voice phrase ready in input box — press Send:";
    userInput.value = sampleVoiceText;
    userInput.focus();
  }

  btnCancelMic.addEventListener("click", function () {
    if (recognition && isRecording) {
      try { recognition.abort(); } catch (e) {}
    }
    stopMicUI();
  });

  btnMic.addEventListener("click", function () {
    var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      showVoiceFallbackHelper("Browser voice API blocked in this frame.");
      return;
    }
    if (isRecording && recognition) {
      try { recognition.stop(); } catch (e) {}
      return;
    }

    try {
      recognition = new SpeechRec();
      recognition.lang = voiceLangSelect.value || "en-IN";
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      var finalTranscript = "";

      recognition.onstart = function () {
        isRecording = true;
        btnMic.textContent = "Stop";
        btnMic.className = "icon-btn recording";
        micStatusText.textContent = "Listening (" + recognition.lang + ")... Speak into your microphone.";
        micStatusBanner.className = "mic-status-banner visible";
      };

      recognition.onresult = function (event) {
        var interim = "";
        for (var i = event.resultIndex; i < event.results.length; i++) {
          var trans = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += trans;
          } else {
            interim += trans;
          }
        }
        userInput.value = (finalTranscript || interim).trim();
        micStatusText.textContent = "Heard: \"" + userInput.value + "\"";
      };

      recognition.onend = function () {
        var spoken = userInput.value.trim();
        stopMicUI();
        if (spoken) {
          sendUserMessage(spoken);
        }
      };

      recognition.onerror = function (ev) {
        stopMicUI();
        if (ev && (ev.error === "not-allowed" || ev.error === "service-not-allowed" || ev.error === "audio-capture")) {
          showVoiceFallbackHelper("Microphone permission blocked by browser/frame.");
        } else {
          showVoiceFallbackHelper("Voice capture ready.");
        }
      };

      recognition.start();
    } catch (err) {
      stopMicUI();
      showVoiceFallbackHelper("Voice input simulated in this preview.");
    }
  });

  // Catalog Modal
  btnOpenCatalog.addEventListener("click", function () {
    catalogModal.className = "modal-backdrop open";
  });
  btnCloseCatalog.addEventListener("click", function () {
    catalogModal.className = "modal-backdrop";
  });

  // Initialize chat
  resetChat();
})();
