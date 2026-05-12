"""
Tool: Crawl4AI로 웹 페이지 종합 분석

한 번의 크롤링으로 다음을 모두 추출
- 페이지 텍스트 (마크다운)
- 메타 태그 (title, description, OG 태그 등)
- 링크 통계 (내부/외부 링크 수, 외부 도메인 목록)

"""

import asyncio
import re
from urllib.parse import urlparse
from langchain_core.tools import tool
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from agent.config import CRAWL4AI_HEADLESS


def _extract_meta_from_html(html: str) -> list[dict]:
    """HTML에서 <meta> 태그를 정규식으로 추출합니다."""
    metas = []
    # name/property → content 순서
    p1 = re.compile(
        r'<meta\s+[^>]*?(?:name|property)\s*=\s*["\']([^"\']+)["\']'
        r'[^>]*?content\s*=\s*["\']([^"\']*)["\']',
        re.IGNORECASE,
    )
    for m in p1.finditer(html[:30000]):
        metas.append({"name": m.group(1), "content": m.group(2)})

    # content → name/property 순서 (역순 배치도 처리)
    p2 = re.compile(
        r'<meta\s+[^>]*?content\s*=\s*["\']([^"\']*)["\']'
        r'[^>]*?(?:name|property)\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    for m in p2.finditer(html[:30000]):
        metas.append({"name": m.group(2), "content": m.group(1)})

    return metas


def _summarize_links(links: dict) -> str:
    """링크 정보를 요약합니다. 판단 없이 사실만 나열합니다."""
    internal = links.get("internal", [])
    external = links.get("external", [])

    # 외부 도메인 추출
    external_domains = set()
    for link in external:
        href = link.get("href", "")
        try:
            domain = urlparse(href).netloc.lower()
            if domain:
                external_domains.add(domain)
        except Exception:
            pass

    summary = f"내부 링크: {len(internal)}개 | 외부 링크: {len(external)}개"
    summary += f" | 고유 외부 도메인: {len(external_domains)}개"

    if external_domains:
        domains_list = sorted(external_domains)[:15]
        summary += "\n외부 도메인 목록: " + ", ".join(domains_list)
        if len(external_domains) > 15:
            summary += f" ... 외 {len(external_domains) - 15}개"

    return summary



async def _async_crawl(url: str) -> dict:
    """Crawl4AI 비동기 크롤링 (안티봇 우회 옵션 포함)"""
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
        word_count_threshold=0,
        wait_until="domcontentloaded",
        delay_before_return_html=5.0,
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

    # ── 핵심 변경: success=False여도 HTML이 있으면 사용 ──
    has_html = bool(result.html and len(result.html) > 100)

    if not result.success and not has_html:
        # HTML도 없으면 진짜 실패
        return {"success": False, "error": result.error_message or "크롤링 실패"}

    if not result.success and has_html:
        # HTML은 있지만 Crawl4AI가 오판한 경우
        print(f"⚠️ [CRAWL] Crawl4AI 검증 실패했으나 HTML 존재 ({len(result.html)} bytes) → 계속 진행")

    # markdown 타입 분기 처리
    md = result.markdown
    if hasattr(md, "raw_markdown"):
        markdown_text = md.raw_markdown or ""
    elif isinstance(md, str):
        markdown_text = md
    else:
        markdown_text = ""

    # markdown이 비어있으면 HTML에서 직접 텍스트 추출 시도
    if not markdown_text and has_html:
        import re
        # script, style 태그 제거 후 텍스트만 추출
        text = re.sub(r'<script[^>]*>.*?</script>', '', result.html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        markdown_text = text if text else "(페이지에 텍스트 콘텐츠 없음 — JS 리다이렉트 또는 빈 페이지)"

    return {
        "success": True,
        "url": result.url,
        "status_code": getattr(result, "status_code", 200),
        "markdown": markdown_text,
        "html": result.html or "",
        "metadata": result.metadata or {},
        "links": result.links or {"internal": [], "external": []},
    }


@tool
def crawl_page(url: str) -> str:
    """
    URL의 웹 페이지를 크롤링하여 콘텐츠를 추출
    페이지 텍스트(마크다운), 메타태그, 링크 정보가 포함
    이 도구를 가장 먼저 사용하세요. 대부분의 사이트는 이 결과만으로 판별 가능
    """
    print(f"\n🌐 [CRAWL] 크롤링 시작: {url}")
    result = asyncio.run(_async_crawl(url))

    if not result["success"]:
        print(f"❌ [CRAWL] 크롤링 실패: {result['error']}")

        return f"크롤링 실패: {result['error']}\nURL: {url}"

    # ── 메타태그 ─────────────────────────
    metadata = result["metadata"]
    title = metadata.get("title", "(제목 없음)")

    print(f"✅ [CRAWL] 크롤링 완료")
    print(f"   제목: {title}")
    print(f"   텍스트 길이: {len(result['markdown'])}자")
    print(f"   내부 링크: {len(result['links'].get('internal', []))}개")
    print(f"   외부 링크: {len(result['links'].get('external', []))}개")
    
    description = metadata.get("description", "(설명 없음)")

    html_metas = _extract_meta_from_html(result["html"])

    # 필터링, 나중에 빼도 괜찮
    important_metas = [
        m for m in html_metas
        if any(m["name"].lower().startswith(p) for p in
               ("og:", "twitter:", "keyword", "description"))
    ]

    # ── 링크 요약 ────────────────────────
    link_summary = _summarize_links(result["links"])

    # ── 텍스트 (토큰 절약) ───────────────
    markdown = result["markdown"]
    MAX_CHARS = 6000
    if len(markdown) > MAX_CHARS:
        markdown = (
            markdown[:MAX_CHARS]
            + f"\n\n... ({len(result['markdown'])}자 중 {MAX_CHARS}자 표시)"
        )

    # ── 출력 ─────────────────────────────
    output = f"""URL: {result['url']}
HTTP 상태: {result['status_code']}

[메타데이터]
제목: {title}
설명: {description}"""

    if important_metas:
        output += "\n주요 메타태그:"
        for m in important_metas[:8]:
            output += f"\n  {m['name']}: {m['content'][:150]}"

    output += f"""

[링크]
{link_summary}

[페이지 텍스트]
{markdown}"""

    return output