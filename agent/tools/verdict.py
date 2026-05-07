"""
Tool: 최종 판별

에이전트가 "근거가 충분하다"고 판단했을 때 호출
이 Tool이 호출되면 분석이 종료
"""

import json
from langchain_core.tools import tool

VALID_CATEGORIES = {
    "adult",          # 음란
    "gamble",         # 도박
    "fraud_verify",   # 먹튀검증
    "link_hub",       # 주소모음
    "harmful_other",  # 기타 유해
    "safe",           # 정상 (삭제 대상 아님)
}

CATEGORY_LABELS = {
    "adult": "음란",
    "gamble": "도박",
    "fraud_verify": "먹튀검증",
    "link_hub": "주소모음",
    "harmful_other": "기타 유해",
    "safe": "정상 (삭제 대상 아님)",
}


@tool
def make_verdict(
    category: str,
    confidence: float,
    evidence_summary: str,
) -> str:
    """
    사이트에 대한 최종 판별을 내립니다. 충분한 근거를 수집한 후 호출
    이 도구를 호출하면 분석이 종료됩니다.

    Args:
        category: 반드시 다음 중 하나:
            'adult'(음란), 'gamble'(도박), 'fraud_verify'(먹튀검증),
            'link_hub'(주소모음), 'harmful_other'(기타 유해), 'safe'(정상)
        confidence: 판별 신뢰도 (0.0 ~ 1.0)
        evidence_summary: 판별 근거 요약 (한국어, 핵심만 간결하게)
    """
    # 카테고리 검증

    print(f"\n🏁 [VERDICT] 최종 판별 호출")
    print(f"   카테고리: {category}")
    print(f"   신뢰도: {confidence}")
    print(f"   근거: {evidence_summary[:100]}")

    if category not in VALID_CATEGORIES:
        return json.dumps({
            "success": False,
            "error": f"잘못된 카테고리: '{category}'",
            "valid_categories": sorted(VALID_CATEGORIES),
        }, ensure_ascii=False)

    # confidence 범위 클램프
    confidence = max(0.0, min(1.0, round(confidence, 2)))

    result = {
        "success": True,
        "category": category,
        "category_label": CATEGORY_LABELS[category],
        "confidence": confidence,
        "evidence_summary": evidence_summary,
    }

    return json.dumps(result, ensure_ascii=False)