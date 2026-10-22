"""
salesgpt
========
WaveNxD AI Sales Representative Package.
Implements a stage-aware, context-aware consultative sales agent for WaveNxD ultrasonic spray nozzles.
"""

from salesgpt.agent import SalesAgent
from salesgpt.catalog import WaveNxDCatalog
from salesgpt.multilingual import detect_language
from salesgpt.stages import ConversationStage, get_stage_info
from salesgpt.tools import generate_ics_calendar_invite, search_product_catalog, send_quotation_email

__version__ = "2.0.0"
__all__ = [
    "SalesAgent",
    "WaveNxDCatalog",
    "ConversationStage",
    "get_stage_info",
    "detect_language",
    "search_product_catalog",
    "send_quotation_email",
    "generate_ics_calendar_invite",
]
