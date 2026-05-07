"""
Tool: whois_lookup — 도메인 WHOIS 등록 정보 조회

도메인의 등록일, 만료일, 등록기관 등을 조회합니다.
최근 등록된 도메인은 불법 사이트일 가능성이 높습니다.

기존 RDAPValidator 모듈의 WHOIS fallback 로직을 Tool 형식으로 재구성했습니다.
"""

from datetime import datetime, timezone
from urllib.parse import urlparse
from langchain_core.tools import tool

import tldextract


def _extract_domain(url: str) -> str:
    """URL에서 루트 도메인 추출 (서브도메인 제거)"""
    if not url.startswith("http"):
        url = f"http://{url}"
    parsed = urlparse(url)
    host = parsed.hostname or url
    ext = tldextract.extract(host)
    return ext.registered_domain or host


def _format_date(date_val) -> str:
    """다양한 형태의 날짜를 문자열로 변환"""
    if date_val is None:
        return "(정보 없음)"
    if isinstance(date_val, list):
        date_val = date_val[0]
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    return str(date_val)


def _days_since(date_val) -> int | None:
    """날짜로부터 경과 일수 계산"""
    if date_val is None:
        return None
    if isinstance(date_val, list):
        date_val = date_val[0]
    if isinstance(date_val, datetime):
        if date_val.tzinfo is None:
            date_val = date_val.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - date_val).days
    return None


@tool
def whois_lookup(url: str) -> str:
    """
    도메인의 등록 정보를 조회합니다. (RDAP 우선, WHOIS fallback)
    등록일, 만료일, 등록기관, 도메인 나이를 확인합니다.
    최근 등록된 도메인이면 불법 사이트일 가능성이 높습니다.
    URL 또는 도메인 모두 입력 가능합니다.
    """
    domain = _extract_domain(url)
    print(f"\n🔍 [WHOIS] 도메인 조회 시작: {domain}")

    try:
        import whois
        w = whois.whois(domain)
    except Exception as e:
        print(f"❌ [WHOIS] 조회 실패: {str(e)[:80]}")
        return (
            f"[WHOIS 결과] 조회 실패\n"
            f"도메인: {domain}\n"
            f"사유: {str(e)[:80]}\n"
            f"참고: 프라이버시 보호 또는 특수 TLD일 수 있음"
        )

    creation_date = w.creation_date
    days = _days_since(creation_date)

    if days is not None:
        if days < 90:
            age_note = "매우 최근 등록 (3개월 미만) — 의심"
        elif days < 180:
            age_note = "최근 등록 (6개월 미만) — 주의"
        elif days < 365:
            age_note = "비교적 최근 등록 (1년 미만)"
        else:
            age_note = f"등록 {days // 365}년 경과 — 안정적"
    else:
        age_note = "등록일 확인 불가"

    print(f"✅ [WHOIS] 조회 완료")
    print(f"   등록기관: {w.registrar or '(정보 없음)'}")
    print(f"   등록일: {_format_date(creation_date)}")
    print(f"   도메인 나이: {age_note}")

    ns = w.name_servers or []
    if isinstance(ns, str):
        ns = [ns]
    ns_list = [str(n).lower() for n in ns[:3]]

    return (
        f"[WHOIS 결과]\n"
        f"도메인: {domain}\n"
        f"등록기관: {w.registrar or '(정보 없음)'}\n"
        f"등록일: {_format_date(creation_date)}\n"
        f"만료일: {_format_date(w.expiration_date)}\n"
        f"경과일: {days if days is not None else '(확인 불가)'}일\n"
        f"도메인 나이: {age_note}\n"
        f"네임서버: {', '.join(ns_list) if ns_list else '(정보 없음)'}"
    )