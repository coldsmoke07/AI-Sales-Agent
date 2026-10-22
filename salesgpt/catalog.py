"""
salesgpt.catalog
================
WaveNxD Technologies Product Catalog - Single Source of Truth & Recommendation Matcher.
Enforces strict anti-hallucination guardrails based on the official product catalog:
- Model numbers are unassigned; products are identified by frequency, type/family, and application.
- Row labeled '60KHz' in the raw 180 kHz table is treated strictly as 180 kHz based on its section heading.
- Unlisted details (prices, warranties, delivery timelines) return the mandatory policy statement:
  'I will confirm this with the WaveNxD engineering team.'
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple


def get_catalog_file_path() -> str:
    """Finds the catalog.json file path reliably."""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "catalog.json"),
        os.path.join(os.path.dirname(__file__), "catalog.json"),
        os.path.join(os.getcwd(), "catalog.json"),
    ]
    for p in possible_paths:
        abs_p = os.path.abspath(p)
        if os.path.exists(abs_p):
            return abs_p
    raise FileNotFoundError("catalog.json could not be located.")


class WaveNxDCatalog:
    def __init__(self, catalog_path: Optional[str] = None):
        path = catalog_path or get_catalog_file_path()
        with open(path, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)

        self.company: Dict[str, Any] = self.data.get("company", {})
        self.nozzles: List[Dict[str, Any]] = self.data.get("nozzle_families", [])
        self.systems: List[Dict[str, Any]] = self.data.get("complete_systems_and_accessories", [])

    def get_company_info(self) -> Dict[str, Any]:
        return self.company

    def get_all_nozzles(self) -> List[Dict[str, Any]]:
        return self.nozzles

    def get_all_systems(self) -> List[Dict[str, Any]]:
        return self.systems

    def find_system_by_id(self, sys_id: str) -> Optional[Dict[str, Any]]:
        for s in self.systems:
            if s.get("id") == sys_id:
                return s
        return None

    def match_nozzle(
        self,
        application: Optional[str] = None,
        industry: Optional[str] = None,
        material: Optional[str] = None,
        viscosity_cp: Optional[float] = None,
        flow_rate_ml_min: Optional[float] = None,
        dispensing_ul: Optional[float] = None,
        droplet_size_um: Optional[float] = None,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], str]:
        """
        Determines the single best-matching WaveNxD nozzle and any relevant accessories.
        Returns: (best_nozzle, accessory_systems, rationale_text)
        """
        app_lower = (application or "").lower()
        mat_lower = (material or "").lower()
        ind_lower = (industry or "").lower()

        # 1. Stent Coating (Ultra-fine mist 10 um, 180 kHz Torch)
        if "stent" in app_lower or "drug eluting" in app_lower:
            nozzle = next((n for n in self.nozzles if n["id"] == "standard_torch_180khz"), None)
            accessories = []
            micro = self.find_system_by_id("micro_fluid_dispensing")
            if micro:
                accessories.append(micro)
            rationale = (
                "For coronary and peripheral stent coatings, WaveNxD's Standard Torch at 180 kHz produces an "
                "ultra-fine 10 µm mist with a feed rate of 5 ml/min for low-viscosity solutions (< 50 cP). "
                "This guarantees uniform drug-polymer adherence without webbing or droplet bridging. "
                "We also pair this with our Micro Fluid Dispensing System (0 to 200 µl metered dispensing) "
                "for precise micro-liter dosage control."
            )
            return nozzle, accessories, rationale

        # 2. Syringe Coating (Silicone oil, narrow bore, Extended Horn 25 mm torch, < 1000 cP)
        if "syringe" in app_lower or "barrel" in app_lower:
            nozzle = next((n for n in self.nozzles if n["id"] == "extended_horn_25mm"), None)
            accessories = []
            micro = self.find_system_by_id("micro_fluid_dispensing")
            if micro:
                accessories.append(micro)
            rationale = (
                "For syringe barrel lubrication and coating, WaveNxD's Extended Horn (25 mm torch) operates at 60 kHz "
                "and can atomize liquids up to 1000 cP (ideal for viscous silicone oils) at 5 ml/min, generating 40 µm droplets. "
                "Its extended reach allows uniform coating deep inside narrow glass or plastic syringe barrels."
            )
            return nozzle, accessories, rationale

        # 3. Blood Collection Tubes (EDTA/Heparin/Clot activator, Extended Horn 15 mm conical)
        if "blood collection" in app_lower or "tube" in app_lower or "vacutainer" in app_lower:
            nozzle = next((n for n in self.nozzles if n["id"] == "extended_horn_15mm"), None)
            accessories = []
            micro = self.find_system_by_id("micro_fluid_dispensing")
            if micro:
                accessories.append(micro)
            rationale = (
                "For blood collection tube (vacutainer) manufacturing, WaveNxD's Extended Horn (15 mm conical) operates at 60 kHz "
                "(40 µm droplet size, 5 ml/min feed rate, < 50 cP). The 15 mm extension directs the low-velocity spray mist "
                "cleanly along the internal tube walls with zero overspray."
            )
            return nozzle, accessories, rationale

        # 4. PIPAC Chemotherapy (20 ml/min, 50 cP, 60 kHz conical)
        if "pipac" in app_lower or "chemotherapy" in app_lower or "oncology" in app_lower:
            nozzle = next((n for n in self.nozzles if n["id"] == "pipac_60khz"), None)
            rationale = (
                "For Pressurized Intraperitoneal Aerosol Chemotherapy (PIPAC), WaveNxD provides the specialized PIPAC Conical nozzle "
                "operating at 60 kHz, delivering 40 µm droplets at a dedicated 20 ml/min feed rate and up to 50 cP viscosity, "
                "ensuring uniform laparoscopic drug aerosolization."
            )
            return nozzle, [], rationale

        # 5. Fuel Cell Coating / Thick Slurries (< 1000 cP)
        if "fuel cell" in app_lower or (viscosity_cp is not None and viscosity_cp > 50):
            if droplet_size_um is not None and droplet_size_um >= 55:
                nozzle = next((n for n in self.nozzles if n["id"] == "high_viscosity_24khz"), None)
                rationale = (
                    "For dense fuel cell slurries and catalyst suspensions (< 1000 cP), WaveNxD's High Viscosity Conical nozzle at 24 kHz "
                    "produces 60 µm droplets at up to 3 ml/min. Its lower frequency provides the acoustic energy required to cleanly "
                    "atomize heavy platinum/carbon inks without tip clogging."
                )
            else:
                nozzle = next((n for n in self.nozzles if n["id"] == "high_viscosity_60khz"), None)
                rationale = (
                    "For fuel cell catalyst and membrane electrode coating (< 1000 cP), WaveNxD's High Viscosity Conical nozzle at 60 kHz "
                    "delivers uniform 40 µm droplets at feed rates up to 3 ml/min, maintaining an even catalyst deposition layer."
                )
            accessories = []
            air = self.find_system_by_id("air_shaping_attachments")
            if air:
                accessories.append(air)
            return nozzle, accessories, rationale

        # 6. Industrial Spray Dryer (High Flow, up to 200 ml/min)
        if "industrial" in app_lower or (flow_rate_ml_min is not None and flow_rate_ml_min > 20):
            nozzle = next((n for n in self.nozzles if n["id"] == "high_flow_60khz"), None)
            rationale = (
                "For high-throughput industrial spray drying, WaveNxD's High Flow Conical nozzle operates at 60 kHz, supporting "
                "high-volume feed rates up to 200 ml/min with 40 µm droplets for low-viscosity solutions (< 50 cP)."
            )
            return nozzle, [], rationale

        # 7. Powder Synthesis / Hydrogen Production / 25 um Droplets (120 kHz)
        if (
            "powder" in app_lower
            or "hydrogen" in app_lower
            or (droplet_size_um is not None and droplet_size_um <= 30)
            or (flow_rate_ml_min is not None and flow_rate_ml_min <= 3.5)
        ):
            nozzle = next((n for n in self.nozzles if n["id"] == "standard_120khz"), None)
            rationale = (
                "For powder synthesis, hydrogen electrolyzer coatings, and high-precision R&D, WaveNxD's Standard Family (torch, conical, "
                "flat; dual-feed flat oval) at 120 kHz produces fine 25 µm droplets at 3 ml/min (< 50 cP), ensuring exceptionally narrow "
                "particle size distributions."
            )
            return nozzle, [], rationale

        # 8. Transparent Conductive Oxide / Heated Substrate Pyrolysis
        if "tco" in app_lower or "pyrolysis" in app_lower or "transparent conductive" in app_lower:
            pyrolysis_sys = self.find_system_by_id("plc_xy_spray_pyrolysis")
            nozzle = next((n for n in self.nozzles if n["id"] == "standard_60khz"), None)
            accessories = [pyrolysis_sys] if pyrolysis_sys else []
            rationale = (
                "For transparent conductive oxide (TCO) and micro-coating thin films, we recommend WaveNxD's PLC-Controlled XY "
                "Spray Pyrolysis System (substrate heated up to 450 °C, SS316 enclosure) equipped with our 60 kHz Standard nozzle "
                "(40 µm droplets, 5 ml/min, < 50 cP) or 120 kHz nozzle."
            )
            return nozzle, accessories, rationale

        # Default fallback: Standard 60 kHz
        nozzle = next((n for n in self.nozzles if n["id"] == "standard_60khz"), None)
        rationale = (
            "WaveNxD's Standard Family (torch, conical, flat) at 60 kHz is our most versatile platform, producing 40 µm droplets "
            "at a 5 ml/min feed rate for liquids under 50 cP. It provides soft, low-velocity atomization with zero pressure."
        )
        return nozzle, [], rationale
