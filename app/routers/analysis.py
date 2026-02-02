from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional
from app.services.pubmed import search_pubmed, fetch_paper_details
from app.services.analyzer import analyze_keywords, analyze_trends, analyze_authors
from app.services.ai_summary import summarize_paper, summarize_multiple_papers, chat_with_papers
from app.models.schemas import (
    KeywordAnalysis,
    TrendAnalysis,
    AuthorAnalysis,
    SummarizeRequest,
    SummaryResponse,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.get("/analyze/keywords", response_model=list[KeywordAnalysis])
async def get_keyword_analysis(
    query: str = Query(..., description="검색 키워드"),
    author: Optional[str] = Query(None, description="저자명"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY)"),
    top_n: int = Query(20, ge=1, le=50, description="상위 N개 키워드"),
):
    """검색 결과에서 키워드 빈도를 분석합니다."""

    try:
        # 분석을 위해 최대 100개 논문 가져오기
        _, pmids = await search_pubmed(
            query=query,
            author=author,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=100,
        )

        papers = await fetch_paper_details(pmids) if pmids else []
        return analyze_keywords(papers, top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@router.get("/analyze/trends", response_model=list[TrendAnalysis])
async def get_trend_analysis(
    query: str = Query(..., description="검색 키워드"),
    author: Optional[str] = Query(None, description="저자명"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY)"),
):
    """연도별 논문 수 트렌드를 분석합니다."""

    try:
        _, pmids = await search_pubmed(
            query=query,
            author=author,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=100,
        )

        papers = await fetch_paper_details(pmids) if pmids else []
        return analyze_trends(papers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@router.get("/analyze/authors", response_model=list[AuthorAnalysis])
async def get_author_analysis(
    query: str = Query(..., description="검색 키워드"),
    author: Optional[str] = Query(None, description="저자명"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY)"),
    top_n: int = Query(20, ge=1, le=50, description="상위 N명 저자"),
):
    """저자별 논문 수를 분석합니다."""

    try:
        _, pmids = await search_pubmed(
            query=query,
            author=author,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=100,
        )

        papers = await fetch_paper_details(pmids) if pmids else []
        return analyze_authors(papers, top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@router.post("/summarize", response_model=SummaryResponse)
async def summarize(request: SummarizeRequest):
    """선택한 논문들을 AI로 요약합니다."""

    try:
        papers = await fetch_paper_details(request.pmids)

        if not papers:
            raise HTTPException(status_code=404, detail="논문을 찾을 수 없습니다.")

        if len(papers) == 1:
            summary = await summarize_paper(papers[0], request.language)
        else:
            summary = await summarize_multiple_papers(papers, request.language)

        return SummaryResponse(summary=summary, pmids=request.pmids)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 중 오류 발생: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """선택한 논문들을 기반으로 AI와 대화합니다."""

    try:
        papers = await fetch_paper_details(request.pmids)

        if not papers:
            raise HTTPException(status_code=404, detail="논문을 찾을 수 없습니다.")

        # 대화 기록 변환
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]

        response = await chat_with_papers(
            papers=papers,
            user_message=request.message,
            chat_history=history,
            language=request.language,
        )

        return ChatResponse(response=response, pmids=request.pmids)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 중 오류 발생: {str(e)}")
