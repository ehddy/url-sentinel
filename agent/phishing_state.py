"""
피싱 에이전트 State 스키마
"""

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class PhishingAnalysisState(TypedDict):
    messages: Annotated[list, add_messages]
    url: str
    category: str | None       # "phishing" | "safe"
    confidence: float | None
    evidence_summary: str | None