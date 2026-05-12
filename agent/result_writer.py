"""
분석 결과를 JSON 파일로 저장하는 유틸리티
결과 파일은 results/{agent_type}_{domain}_{timestamp}.json 형태로 저장됩니다.
"""

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse


RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


def save_result(agent_type: str, result: dict) -> str:
    """
    분석 결과를 JSON 파일로 저장합니다.

    Args:
        agent_type: "category" 또는 "phishing"
        result:     graph.invoke() 반환값

    Returns:
        저장된 파일 경로
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)

    url = result.get("url", "unknown")
    domain = urlparse(url).netloc.replace(":", "_") or "unknown"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{agent_type}_{domain}_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)

    payload = {
        "agent_type": agent_type,
        "model_id": result.get("model_id"),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "category": result.get("category"),
        "confidence": result.get("confidence"),
        "evidence_summary": result.get("evidence_summary"),
        "token_usage": result.get("token_usage"),
        "processing_time_seconds": result.get("processing_time_seconds"),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return filepath
