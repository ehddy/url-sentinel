"""
Tool: dns_check — DNS 조회로 사이트 생존 확인

사이트가 살아있는지 빠르게 확인합니다. (1초 이내)
죽은 사이트는 크롤링할 필요 없이 바로 '삭제'로 처리

기존 DNSValidator 모듈의 핵심 로직을 Tool 형식으로 재구성
"""

import socket
from urllib.parse import urlparse
from langchain_core.tools import tool


def _extract_host(url: str) -> str:
    """URL에서 호스트명 추출"""
    if not url.startswith("http"):
        url = f"http://{url}"
    parsed = urlparse(url)
    return parsed.hostname or url


@tool
def dns_check(url: str) -> str:
    """
    URL의 DNS를 조회하여 사이트가 살아있는지 확인합니다.
    이 도구는 매우 빠르게 실행됩니다 (1초 이내).
    사이트가 죽어있으면 크롤링이 불필요하므로, 가장 먼저 사용하는 것을 권장합니다.
    """
    host = _extract_host(url)
    print(f"\n🌐 [DNS] 생존 확인: {host}")

    try:
        results = socket.getaddrinfo(host, 80, socket.AF_INET, socket.SOCK_STREAM)
        if results:
            ip = results[0][4][0]
            print(f"✅ [DNS] 생존 | IP: {ip}")
            return f"[DNS 결과] 상태: 생존 | 호스트: {host} | IP: {ip}"
        else:
            print(f"💀 [DNS] 죽음 | DNS 레코드 없음")
            return f"[DNS 결과] 상태: 죽음 | 호스트: {host} | 사유: DNS 레코드 없음"

    except socket.gaierror as e:
        print(f"💀 [DNS] 죽음 | {e}")
        return f"[DNS 결과] 상태: 죽음 | 호스트: {host} | 사유: DNS 조회 실패 ({e})"

    except socket.timeout:
        print(f"💀 [DNS] 죽음 | 타임아웃")
        return f"[DNS 결과] 상태: 죽음 | 호스트: {host} | 사유: DNS 타임아웃"

    except Exception as e:
        print(f"⚠️ [DNS] 불명 | {e}")
        return f"[DNS 결과] 상태: 불명 | 호스트: {host} | 사유: {str(e)[:80]}"