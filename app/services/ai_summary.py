from groq import AsyncGroq
from app.config import GROQ_API_KEY
from app.models.schemas import Paper
from typing import Optional
import json


# 전문분야별 프롬프트 설정
SPECIALTY_PROMPTS = {
    "radiology": """당신은 의학 논문 분석 전문가입니다.
일반적인 의사가 이해할 수 있도록 논문을 명확하게 요약해주세요.
연구의 목적, 방법론, 주요 결과, 임상적 의의를 포함해야 합니다.""",

    "general": """당신은 의학 논문 분석 전문가입니다.
연구의 목적, 방법론, 주요 결과, 임상적 의의를 명확하게 요약해주세요."""
}

# 인터벤션 영상의학과 전용 추가 분석
IR_INSIGHT_PROMPT = """
추가로, 인터벤션 영상의학과(Interventional Radiology) 전문의 관점에서 다음 사항이 있다면 분석해주세요:
- 영상 유도 시술 관련 내용 (CT/US/Fluoro guided procedure)
- 혈관 접근법, 카테터/와이어 선택, 색전술 기법
- 시술 성공률, 합병증, 기술적 고려사항
- 종양 치료 (TACE, RFA, MWA, Cryo 등) 관련 내용
- 혈관 중재술 (스텐트, 혈전제거술, TIPS 등) 관련 내용
- 비혈관 중재술 (배액술, 생검, 척추성형술 등) 관련 내용
해당 내용이 없으면 이 섹션은 "해당 없음"으로 표시하세요."""


async def summarize_paper(
    paper: Paper,
    language: str = "korean",
    specialty: str = "radiology"
) -> str:
    """단일 논문의 초록을 전문분야에 맞게 요약합니다."""

    if not GROQ_API_KEY:
        return "Groq API 키가 설정되지 않았습니다."

    if not paper.abstract:
        return "초록이 없습니다."

    client = AsyncGroq(api_key=GROQ_API_KEY)

    lang_instruction = "한국어로 작성해주세요." if language == "korean" else "Please write in English."
    specialty_prompt = SPECIALTY_PROMPTS.get(specialty, SPECIALTY_PROMPTS["general"])

    ir_section = IR_INSIGHT_PROMPT if specialty == "radiology" else ""

    prompt = f"""{specialty_prompt}

{lang_instruction}

## 논문 정보
**제목**: {paper.title}
**저널**: {paper.journal}
**출판일**: {paper.pub_date}
**초록**: {paper.abstract}

## 요약 형식
다음 구조로 요약해주세요:

### 📋 연구 개요
(연구 목적과 배경을 간결하게)

### 🔬 연구 방법
(대상, 연구 설계, 분석 방법)

### 📊 주요 결과
(핵심 수치와 통계적 유의성)

### 💡 임상적 의의
(실제 진료에 적용할 수 있는 포인트)

### ⚠️ 제한점
(연구의 한계, 있다면)
{ir_section}
### 🩺 인터벤션 영상의학과 관점
(위 분석 내용 작성)
"""

    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.3,
    )

    return response.choices[0].message.content or "요약을 생성할 수 없습니다."


async def summarize_multiple_papers(
    papers: list[Paper],
    language: str = "korean",
    specialty: str = "radiology"
) -> str:
    """여러 논문의 공통 주제와 결론을 전문분야에 맞게 종합 요약합니다."""

    if not GROQ_API_KEY:
        return "Groq API 키가 설정되지 않았습니다."

    if not papers:
        return "요약할 논문이 없습니다."

    client = AsyncGroq(api_key=GROQ_API_KEY)

    lang_instruction = "한국어로 작성해주세요." if language == "korean" else "Please write in English."
    specialty_prompt = SPECIALTY_PROMPTS.get(specialty, SPECIALTY_PROMPTS["general"])

    # 논문 정보 정리
    papers_info = []
    for i, paper in enumerate(papers[:10], 1):
        abstract = paper.abstract[:600] if len(paper.abstract) > 600 else paper.abstract
        papers_info.append(
            f"**[논문 {i}]**\n"
            f"- 제목: {paper.title}\n"
            f"- 저널: {paper.journal} ({paper.pub_date})\n"
            f"- 초록: {abstract}"
        )

    papers_text = "\n\n".join(papers_info)

    ir_section = IR_INSIGHT_PROMPT if specialty == "radiology" else ""

    prompt = f"""{specialty_prompt}

{lang_instruction}

## 분석할 논문 목록 ({len(papers)}편)

{papers_text}

## 종합 분석 형식
다음 구조로 종합 분석해주세요:

### 📚 연구 동향 개요
(이 논문들이 다루는 공통 주제와 연구 트렌드)

### 🔍 주요 연구 방법 비교
(환자군, 연구 설계, 분석 방법의 공통점과 차이점)

### 📊 핵심 발견 종합
(여러 연구에서 일관되게 나타나는 결과, 상충되는 결과가 있다면 언급)

### 💡 임상 적용 포인트
(의사가 실무에서 참고할 수 있는 핵심 사항)

### 🔮 향후 연구 방향
(현재 연구의 한계와 필요한 후속 연구)
{ir_section}
### 🩺 인터벤션 영상의학과 관점
(위 분석 내용 작성 - 해당 내용이 없으면 "해당 없음")
"""

    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.3,
    )

    return response.choices[0].message.content or "요약을 생성할 수 없습니다."


async def chat_with_papers(
    papers: list[Paper],
    user_message: str,
    chat_history: list[dict],
    language: str = "korean",
    specialty: str = "radiology"
) -> str:
    """논문 기반으로 AI와 대화합니다."""

    if not GROQ_API_KEY:
        return "Groq API 키가 설정되지 않았습니다."

    if not papers:
        return "선택된 논문이 없습니다."

    client = AsyncGroq(api_key=GROQ_API_KEY)

    lang_instruction = "한국어로 답변해주세요." if language == "korean" else "Please answer in English."
    specialty_context = "사용자는 인터벤션 영상의학과 전문의입니다. 일반적인 의학 관점에서 답변하되, 인터벤션 시술(혈관/비혈관 중재술, 영상유도 시술 등)과 관련된 내용이 있다면 추가로 언급해주세요." if specialty == "radiology" else ""

    # 논문 컨텍스트 생성
    papers_context = []
    for i, paper in enumerate(papers[:10], 1):
        abstract = paper.abstract[:800] if len(paper.abstract) > 800 else paper.abstract
        papers_context.append(
            f"[논문 {i}]\n"
            f"제목: {paper.title}\n"
            f"저자: {', '.join(paper.authors[:5])}\n"
            f"저널: {paper.journal}\n"
            f"출판일: {paper.pub_date}\n"
            f"초록: {abstract}"
        )

    context = "\n\n".join(papers_context)

    system_prompt = f"""당신은 학술 논문 분석 전문가입니다. 사용자가 제공한 논문들을 기반으로 질문에 답변합니다.
{specialty_context}
{lang_instruction}

## 제공된 논문 정보:
{context}

## 답변 가이드라인:
- 제공된 논문 내용을 기반으로 정확하게 답변하세요
- 논문에 없는 내용은 추측하지 말고 "제공된 논문에서 해당 정보를 찾을 수 없습니다"라고 답변하세요
- 가능하면 어떤 논문에서 정보를 가져왔는지 언급하세요
- 답변은 명확하고 구조화된 형식으로 작성하세요
- 영상의학적 관점에서 실용적인 정보를 제공하세요"""

    # 메시지 구성
    messages = [{"role": "system", "content": system_prompt}]

    # 이전 대화 기록 추가 (최근 10개)
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 현재 사용자 메시지 추가
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=1500,
        temperature=0.4,
    )

    return response.choices[0].message.content or "응답을 생성할 수 없습니다."


async def generate_search_query(natural_query: str, language: str = "korean") -> dict:
    """자연어 검색어를 PubMed 검색 쿼리로 변환합니다."""

    if not GROQ_API_KEY:
        return {"error": "Groq API 키가 설정되지 않았습니다."}

    client = AsyncGroq(api_key=GROQ_API_KEY)

    prompt = f"""당신은 PubMed 검색 전문가입니다. 사용자의 자연어 질문을 최적의 PubMed 검색 쿼리로 변환해주세요.

## 사용자 질문
"{natural_query}"

## 변환 규칙
1. 핵심 의학 용어를 영어 MeSH 용어로 변환
2. 적절한 Boolean 연산자 (AND, OR) 사용
3. 필요시 필드 태그 사용 ([Title/Abstract], [MeSH Terms] 등)
4. 너무 좁거나 넓지 않은 적절한 범위의 쿼리 생성

## 출력 형식 (반드시 이 형식으로만 출력)
QUERY: (실제 PubMed 검색 쿼리)
EXPLANATION: (이 쿼리를 선택한 이유, 한국어로 간단히)
KEYWORDS: (핵심 키워드 3-5개, 쉼표로 구분)

예시:
QUERY: (lung cancer[MeSH Terms]) AND (CT scan[Title/Abstract]) AND (diagnosis[MeSH Terms])
EXPLANATION: 폐암의 CT 진단에 관한 논문을 찾기 위해 MeSH 용어와 제목/초록 검색을 조합했습니다.
KEYWORDS: lung cancer, CT, diagnosis, imaging"""

    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.2,
    )

    result_text = response.choices[0].message.content or ""

    # 결과 파싱
    result = {
        "original_query": natural_query,
        "pubmed_query": "",
        "explanation": "",
        "keywords": []
    }

    for line in result_text.split("\n"):
        line = line.strip()
        if line.startswith("QUERY:"):
            result["pubmed_query"] = line.replace("QUERY:", "").strip()
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.replace("EXPLANATION:", "").strip()
        elif line.startswith("KEYWORDS:"):
            keywords = line.replace("KEYWORDS:", "").strip()
            result["keywords"] = [k.strip() for k in keywords.split(",")]

    # 쿼리가 비어있으면 원본 사용
    if not result["pubmed_query"]:
        result["pubmed_query"] = natural_query

    return result


async def detect_ir_related_papers(papers: list[Paper]) -> dict[str, bool]:
    """AI를 사용하여 논문이 인터벤션 영상의학과와 관련있는지 판단합니다."""

    if not GROQ_API_KEY or not papers:
        return {}

    client = AsyncGroq(api_key=GROQ_API_KEY)

    # 논문 정보를 간단히 정리
    papers_info = []
    for paper in papers[:20]:  # 최대 20개
        papers_info.append({
            "pmid": paper.pmid,
            "title": paper.title,
            "abstract": paper.abstract[:300] if paper.abstract else ""
        })

    papers_json = json.dumps(papers_info, ensure_ascii=False)

    prompt = f"""당신은 인터벤션 영상의학과(Interventional Radiology) 전문가입니다.
아래 논문들이 인터벤션 영상의학과와 관련이 있는지 판단해주세요.

## IR 관련 주제 (이 중 하나라도 해당되면 관련있음):
- 혈관 중재술: TACE, TARE, 혈관색전술, 스텐트, TIPS, 혈전제거술, 동맥류 치료
- 비혈관 중재술: 경피적 배액술, 생검, 척추성형술, 신경차단술
- 종양 치료: RFA, MWA, 냉동절제술, IRE
- 영상 유도 시술: CT/US/형광투시 유도 시술
- 혈관 접근: 카테터, 가이드와이어, 천자 기법
- 중재적 종양학: 간암/신장암/폐암 등의 국소치료

## 논문 목록:
{papers_json}

## 출력 형식 (반드시 JSON만 출력):
{{"pmid1": true, "pmid2": false, ...}}

true = IR 관련, false = IR 관련 아님"""

    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1,
        )

        result_text = response.choices[0].message.content or "{}"

        # JSON 파싱 시도
        # JSON 부분만 추출
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        if start != -1 and end > start:
            json_str = result_text[start:end]
            return json.loads(json_str)

        return {}
    except Exception as e:
        print(f"IR 감지 오류: {e}")
        return {}
