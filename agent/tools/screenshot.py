"""
Tool: 스크린샷 캡쳐 + 멀티 모달 

1. Crawl4AI로 페이지 스크린샷을 캡처 (base64 PNG)
2. 별도의 Claude 멀티모달 호출로 이미지를 분석
3. 분석 결과 텍스트를 반환

"""

import asyncio
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_aws import ChatBedrockConverse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from agent.config import BEDROCK_MODEL_ID, AWS_REGION, CRAWL4AI_HEADLESS


VISION_SYSTEM_PROMPT = """\
당신은 웹 페이지 스크린샷을 분석하는 전문가입니다.
이 스크린샷이 어떤 종류의 사이트인지 시각적 요소를 기반으로 분석하세요.

다음을 중점적으로 확인하세요:
- 페이지의 전반적인 레이아웃과 디자인 패턴
- 배너, 광고, 팝업의 내용
- 이미지/썸네일의 성격
- UI 요소 (베팅 폼, 게임 로비, 로그인/충전 버튼 등)
- 텍스트로 된 키워드나 슬로건

분석 결과를 한국어로 간결하게 보고하세요.
"""



async def _async_capture(url: str) -> dict:
    """Crawl4AI로 스크린샷 캡처 (안티봇 우회 옵션 포함)"""
    browser_config = BrowserConfig(
        headless=CRAWL4AI_HEADLESS,
        verbose=False,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        viewport_width=1920,
        viewport_height=1080,
        java_script_enabled=True,
        ignore_https_errors=True,
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-sandbox",
        ],
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        screenshot=True,
        wait_until="networkidle",
        delay_before_return_html=3.0,
        remove_overlay_elements=True,
        page_timeout=30000,
        js_code="""
            const cookieButtons = document.querySelectorAll(
                'button[class*="accept"], button[class*="agree"], button[class*="consent"], '
                + 'a[class*="accept"], a[class*="agree"], [id*="cookie"] button'
            );
            cookieButtons.forEach(btn => btn.click());
        """,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
    except Exception as e:
        return {"success": False, "error": f"브라우저 오류: {str(e)[:80]}"}

    if not result.success:
        return {"success": False, "error": result.error_message or "캡처 실패"}

    if not result.screenshot:
        return {"success": False, "error": "스크린샷이 생성되지 않았습니다"}

    return {
        "success": True,
        "screenshot_b64": result.screenshot,
    }

def _analyze_with_vision(screenshot_b64: str) -> str:
    """멀티모달 Claude로 스크린샷 분석"""
    llm = ChatBedrockConverse(
        model=BEDROCK_MODEL_ID,
        region_name=AWS_REGION,
        temperature=0,
        max_tokens=2048,
    )

    messages = [
        SystemMessage(content=VISION_SYSTEM_PROMPT),
        HumanMessage(content=[
            {
                "type": "text",
                "text": "이 웹 페이지 스크린샷을 분석해주세요. 어떤 종류의 사이트로 보이는지, 시각적 근거를 포함하여 보고하세요.",
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_b64,
                },
            },
        ]),
    ]

    response = llm.invoke(messages)
    return response.content


@tool
def capture_and_analyze(url: str) -> str:
    """
    웹 페이지의 스크린샷을 캡처하고 시각적으로 분석합니다.
    crawl_page의 텍스트 분석만으로 판별이 어려울 때 사용하세요.
    페이지의 레이아웃, 배너, 이미지, UI 요소 등 시각적 근거를 수집합니다.
    """
    # 1) 스크린샷 캡처

    print(f"\n📸 [SCREENSHOT] 스크린샷 캡처 시작: {url}")

    capture_result = asyncio.run(_async_capture(url))

    if not capture_result["success"]:
        print(f"❌ [SCREENSHOT] 캡처 실패: {capture_result['error']}")
        return f"스크린샷 캡처 실패: {capture_result['error']}\nURL: {url}"

    b64_length = len(capture_result["screenshot_b64"])
    print(f"✅ [SCREENSHOT] 캡처 완료 (base64: {b64_length}자)")
    print(f"👁️ [VISION] 멀티모달 분석 시작...")

    # 2) 멀티모달 분석
    try:
        analysis = _analyze_with_vision(capture_result["screenshot_b64"])
    except Exception as e:
        print(f"❌ [VISION] 분석 실패: {e}")
        return f"시각 분석 실패: {str(e)}\nURL: {url}"

    print(f"✅ [VISION] 분석 완료")
    print(f"   결과 미리보기: {analysis[:100]}...")

    return f"[스크린샷 시각 분석 결과]\nURL: {url}\n\n{analysis}"