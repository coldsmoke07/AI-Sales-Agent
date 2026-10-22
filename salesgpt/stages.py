"""
salesgpt.stages
================
Defines the 7 distinct stages of the consultative sales conversation for WaveNxD ultrasonic spray nozzles.
Adapted from SalesGPT's stage-aware state-machine architecture to map to the 7 evaluation requirements:

1. Greet and introduce
2. Pitch briefly
3. Ask about the client (Requirement discovery)
4. Answer questions (Catalog product queries & multilingual replies)
5. Recommend (Best matching nozzle/system with rationale)
6. Close (Offer quotation by email, collect contact details, schedule follow-up call)
7. Confirm (Summarize requirement, recommendation, and next steps)
"""

from enum import Enum
from typing import Dict


class ConversationStage(str, Enum):
    INTRODUCTION = "1"
    PITCH = "2"
    REQUIREMENT_DISCOVERY = "3"
    PRODUCT_KNOWLEDGE = "4"
    RECOMMENDATION = "5"
    CLOSING_QUOTATION = "6"
    CONFIRMATION = "7"


STAGE_NAMES: Dict[str, str] = {
    ConversationStage.INTRODUCTION: "1. Self-Introduction",
    ConversationStage.PITCH: "2. Ultrasonic Technology Pitch",
    ConversationStage.REQUIREMENT_DISCOVERY: "3. Requirement Discovery",
    ConversationStage.PRODUCT_KNOWLEDGE: "4. Catalog Product Knowledge",
    ConversationStage.RECOMMENDATION: "5. Product Recommendation",
    ConversationStage.CLOSING_QUOTATION: "6. Quotation & Callback Close",
    ConversationStage.CONFIRMATION: "7. Order Confirmation & Summary",
}

STAGE_DESCRIPTIONS: Dict[str, str] = {
    ConversationStage.INTRODUCTION: (
        "Greet the prospective client politely, introduce yourself as Arjun Kulkarni "
        "representing WaveNxD Technologies Pvt. Ltd., Kolhapur, and present WaveNxD's "
        "no-pressure ultrasonic spray nozzle systems."
    ),
    ConversationStage.PITCH: (
        "Briefly explain in 2-3 sentences what an ultrasonic nozzle does: it creates a soft, "
        "low-velocity spray with fine, highly uniform droplets without hydraulic pressure, "
        "preventing clogging and overspray. Mention target industries (medical devices, "
        "pharmaceuticals, electronics, energy, semiconductors)."
    ),
    ConversationStage.REQUIREMENT_DISCOVERY: (
        "Systematically discover the client's engineering parameters: target industry, "
        "specific application, coating liquid/material, liquid viscosity (cP), required feed/flow "
        "rate (ml/min or µl), and target droplet size (µm)."
    ),
    ConversationStage.PRODUCT_KNOWLEDGE: (
        "Accurately answer client questions regarding WaveNxD nozzles strictly based on the "
        "official catalog. Follow anti-hallucination rules: if a spec, price, warranty, or timeline "
        "is unlisted, state: 'I will confirm this with the WaveNxD engineering team'."
    ),
    ConversationStage.RECOMMENDATION: (
        "Recommend the single best-matching nozzle family or complete system from the catalog "
        "and provide a plain-language technical justification explaining why it satisfies their "
        "viscosity, droplet size, and application constraints."
    ),
    ConversationStage.CLOSING_QUOTATION: (
        "Propose sending an official quotation via email. Collect client contact details: "
        "Full Name, Company Name, Email Address, Phone Number, and agreed date/time for a follow-up call."
    ),
    ConversationStage.CONFIRMATION: (
        "Summarize the entire consultation back to the client: requirement parameters, recommended nozzle, "
        "quotation dispatch details, and confirmed follow-up technical call slot."
    ),
}


def get_stage_info(stage_id: str) -> Dict[str, str]:
    """Returns name and description for the given stage id."""
    sid = str(stage_id)
    return {
        "id": sid,
        "name": STAGE_NAMES.get(sid, f"Stage {sid}"),
        "description": STAGE_DESCRIPTIONS.get(sid, ""),
    }
