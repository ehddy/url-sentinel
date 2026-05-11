"""
Tool: virustotal_check — VirusTotal URL 검사

URL을 VirusTotal에 조회하여 보안 벤더들의 탐지 결과를 가져옵니다.
기존 분석 결과가 있으면 바로 반환하고, 없으면 스캔을 요청합니다.
"""

import base64
from langchain_core.tools import tool
from agent.config import VT_API_KEY


@tool
def virustotal_check(url: str) -> str:
    """
    URL을 VirusTotal에 조회하여 보안 업체들의 탐지 결과를 확인합니다.
    악성(malicious), 의심(suspicious), 미탐지(undetected), 정상(harmless) 수를 반환합니다.
    피싱 사이트 판별의 강력한 외부 근거로 활용할 수 있습니다.
    """
    if not VT_API_KEY:
        return "[VirusTotal 실패] API 키가 설정되지 않았습니다. .env의 VT_API_KEY를 확인하세요."

    print(f"\n🛡️ [VT] VirusTotal 조회 시작: {url}")

    try:
        import vt
        client = vt.Client(VT_API_KEY)
    except Exception as e:
        return f"[VirusTotal 실패] 클라이언트 초기화 오류: {str(e)[:80]}"

    try:
        # 1) 기존 분석 결과 조회
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        url_obj = client.get_object(f"/urls/{url_id}")

        stats = url_obj.last_analysis_stats
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        undetected = stats.get("undetected", 0)
        harmless = stats.get("harmless", 0)
        total = malicious + suspicious + undetected + harmless

        print(f"✅ [VT] 기존 결과 발견")
        print(f"   악성: {malicious} | 의심: {suspicious} | 미탐지: {undetected} | 정상: {harmless}")

        # 대표 탐지 벤더 추출 (malicious로 판정한 벤더 이름)
        flagged_vendors = []
        if hasattr(url_obj, "last_analysis_results"):
            for vendor, result in url_obj.last_analysis_results.items():
                if result.get("category") == "malicious":
                    flagged_vendors.append(vendor)

        client.close()

        output = (
            f"[VirusTotal 결과]\n"
            f"URL: {url}\n"
            f"조회 방법: 기존 분석 결과\n"
            f"악성(malicious): {malicious}개\n"
            f"의심(suspicious): {suspicious}개\n"
            f"미탐지(undetected): {undetected}개\n"
            f"정상(harmless): {harmless}개\n"
            f"총 검사 벤더: {total}개\n"
            f"탐지율: {malicious + suspicious}/{total}"
        )

        if flagged_vendors:
            output += f"\n탐지 벤더: {', '.join(flagged_vendors[:10])}"
            if len(flagged_vendors) > 10:
                output += f" 외 {len(flagged_vendors) - 10}개"

        return output

    except Exception as e:
        error_str = str(e)

        # NotFoundError → 스캔 요청
        if "NotFoundError" in error_str:
            print(f"ℹ️ [VT] 기존 결과 없음 → 스캔 요청")
            try:
                analysis = client.scan_url(url, wait_for_completion=True)
                stats = analysis.stats
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                undetected = stats.get("undetected", 0)
                harmless = stats.get("harmless", 0)
                total = malicious + suspicious + undetected + harmless

                print(f"✅ [VT] 스캔 완료")
                print(f"   악성: {malicious} | 의심: {suspicious} | 미탐지: {undetected} | 정상: {harmless}")

                client.close()

                return (
                    f"[VirusTotal 결과]\n"
                    f"URL: {url}\n"
                    f"조회 방법: 신규 스캔\n"
                    f"악성(malicious): {malicious}개\n"
                    f"의심(suspicious): {suspicious}개\n"
                    f"미탐지(undetected): {undetected}개\n"
                    f"정상(harmless): {harmless}개\n"
                    f"총 검사 벤더: {total}개\n"
                    f"탐지율: {malicious + suspicious}/{total}"
                )

            except Exception as scan_err:
                client.close()
                print(f"❌ [VT] 스캔 실패: {scan_err}")
                return f"[VirusTotal 실패] 스캔 오류: {str(scan_err)[:80]}"

        client.close()
        print(f"❌ [VT] 조회 실패: {error_str[:80]}")
        return f"[VirusTotal 실패] {error_str[:80]}"