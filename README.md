# url-sentinel

유해 사이트 분류 및 피싱 탐지를 위한 AI 에이전트 시스템입니다.

## 에이전트 구성

### 1. 유해 카테고리 분류 에이전트 (`main.py`)
URL을 분석하여 다음 6가지 카테고리로 분류합니다.

| 카테고리 | 설명 |
|---|---|
| `adult` | 성인/음란 콘텐츠 |
| `gamble` | 도박 사이트 |
| `fraud_verify` | 먹튀검증 사이트 |
| `link_hub` | 불법 사이트 주소 모음 |
| `harmful_other` | 기타 유해 사이트 |
| `safe` | 정상 또는 접속 불가 사이트 |

### 2. 피싱 탐지 에이전트 (`main_phishing.py`)
URL을 분석하여 피싱 여부를 판별합니다 (`phishing` / `safe`).

> **주의:** 불법 도박, 음란, 먹튀검증 등 유해 사이트라도 사용자를 속여 개인정보를 탈취하려는 의도가 없으면 `safe`로 분류합니다. 이 에이전트의 임무는 오직 "피싱 여부"만 판별합니다.

---

## 사용 도구

에이전트는 다음 도구를 조합하여 판단합니다.

| 도구 | 설명 |
|---|---|
| **dns_check** | 도메인 생존 여부 확인 |
| **crawl_page** | 페이지 텍스트, 메타태그, 링크 추출 (안티봇 우회 적용) |
| **whois_lookup** | 도메인 등록 정보 및 등록일 분석 |
| **google_search** | Google Custom Search를 통한 평판 조회 |
| **capture_and_analyze** | 스크린샷 캡처 + 멀티모달 시각 분석 (안티봇 우회 적용) |
| **virustotal_check** | VirusTotal에 URL 조회 — 보안 벤더들의 악성/의심 탐지 결과 확인 (피싱 탐지 전용) |

### 안티봇 우회

`crawl_page`와 `capture_and_analyze`는 실제 브라우저처럼 동작하도록 다음 옵션이 적용되어 있습니다.

- Chrome User-Agent 위장 및 1920×1080 뷰포트 설정
- `navigator.webdriver = false` 위장 (`--disable-blink-features=AutomationControlled`)
- 쿠키 동의 배너 자동 클릭 JS 실행
- 오버레이 요소 자동 제거 (`remove_overlay_elements`)
- Cloudflare 등 JS 챌린지 대기를 위한 `page_timeout` 설정

---

## 환경 설정

### `.env` 파일 생성

```bash
cp .env.example .env
```

`.env`에 아래 값을 채워주세요.

```dotenv
# AWS Bedrock
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-6

# 브라우저 헤드리스 설정
# 로컬 가상환경: false  /  Docker: true
CRAWL4AI_HEADLESS=false

# Google Custom Search API
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CX=your_cx_here
GOOGLE_SEARCH_DAYS=30

# VirusTotal API (피싱 탐지 에이전트에서 사용)
VT_API_KEY=your_virustotal_api_key_here
```

> **VirusTotal API 키 발급:** https://www.virustotal.com 에서 무료 계정 생성 후 API 키를 발급받을 수 있습니다. 키가 없으면 `virustotal_check` 도구는 건너뜁니다.

---

## 실행 방법

### 방법 1 - 가상환경 (로컬)

#### 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium

# crawl4ai 초기화
crawl4ai-setup
```

#### 실행

```bash
# 유해 카테고리 분류
python main.py https://example.com

# 피싱 탐지
python main_phishing.py https://example.com
```

> 로컬 환경에서는 분석 중 Chromium 브라우저 창이 자동으로 열립니다.
> 브라우저를 숨기려면 `.env`에서 `CRAWL4AI_HEADLESS=true`로 변경하세요.

---

### 방법 2 - Docker

#### 이미지 빌드

```bash
docker compose build
```

#### 실행

```bash
# 유해 카테고리 분류
docker compose run --rm url-agent python main.py https://example.com

# 피싱 탐지
docker compose run --rm url-agent python main_phishing.py https://example.com
```

> Docker 환경에서는 `CRAWL4AI_HEADLESS=true`가 자동 적용되어 브라우저 창이 열리지 않습니다.
> 분석 결과 JSON은 호스트의 `./results/` 폴더에 볼륨 마운트되어 저장됩니다.

---

## 프로젝트 구조

```
url_agent/
├── agent/
│   ├── config.py            # 환경 변수 및 공통 설정
│   ├── result_writer.py     # 분석 결과 JSON 저장 유틸리티
│   ├── graph.py             # 유해 분류 에이전트 워크플로우 (LangGraph)
│   ├── phishing_graph.py    # 피싱 탐지 에이전트 워크플로우 (LangGraph)
│   ├── state.py             # 유해 분류 상태 스키마
│   ├── phishing_state.py    # 피싱 탐지 상태 스키마
│   ├── prompts.py           # 유해 분류 시스템 프롬프트
│   ├── phishing_prompts.py  # 피싱 탐지 시스템 프롬프트
│   └── tools/
│       ├── dns_check.py
│       ├── crawl.py         # 안티봇 우회 옵션 포함
│       ├── whois_lookup.py
│       ├── google_search.py
│       ├── screenshot.py    # 안티봇 우회 옵션 포함
│       ├── verdict.py
│       ├── phishing_verdict.py
│       └── virustotal.py    # VirusTotal URL 조회
├── results/                 # 분석 결과 JSON 저장 폴더 (.gitignore 제외)
├── main.py                  # 유해 분류 실행 엔트리포인트
├── main_phishing.py         # 피싱 탐지 실행 엔트리포인트
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 출력 예시

```
카테고리: gamble
신뢰도: 0.97
근거: 페이지 제목과 본문에 '바카라', '슬롯', '스포츠베팅' 등의 도박 관련 키워드가 다수 발견됨.
      외부 링크 대부분이 알려진 도박 사이트 도메인으로 연결됨.

결과 저장: results/category_example.com_20250507_123456.json
```

### 결과 JSON 형식

분석이 완료되면 `results/` 폴더에 JSON 파일이 자동 저장됩니다.
파일명 형식: `{agent_type}_{domain}_{timestamp}.json`

```json
{
  "agent_type": "category",
  "analyzed_at": "2025-05-07T12:34:56+00:00",
  "url": "https://example.com",
  "category": "gamble",
  "confidence": 0.97,
  "evidence_summary": "페이지 제목과 본문에 '바카라', '슬롯' 등의 도박 관련 키워드가 다수 발견됨."
}
```

> `results/` 폴더는 `.gitignore`에 등록되어 git에 커밋되지 않습니다.
