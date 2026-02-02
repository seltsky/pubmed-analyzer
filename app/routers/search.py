from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.pubmed import search_pubmed, fetch_paper_details, get_paper_by_pmid
from app.services.ai_summary import generate_search_query
from app.models.schemas import SearchResponse, Paper


class NaturalQueryRequest(BaseModel):
    query: str


class NaturalQueryResponse(BaseModel):
    original_query: str
    pubmed_query: str
    explanation: str
    keywords: list[str]

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search_papers(
    query: str = Query(..., description="검색 키워드"),
    author: Optional[str] = Query(None, description="저자명"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 결과 수"),
):
    """PubMed에서 논문을 검색합니다."""

    try:
        total, pmids = await search_pubmed(
            query=query,
            author=author,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

        papers = await fetch_paper_details(pmids) if pmids else []

        return SearchResponse(
            total=total,
            page=page,
            page_size=page_size,
            papers=papers,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@router.get("/paper/{pmid}", response_model=Paper)
async def get_paper(pmid: str):
    """특정 PMID의 논문 상세 정보를 조회합니다."""

    paper = await get_paper_by_pmid(pmid)
    if not paper:
        raise HTTPException(status_code=404, detail="논문을 찾을 수 없습니다.")

    return paper


@router.post("/generate-query", response_model=NaturalQueryResponse)
async def generate_query(request: NaturalQueryRequest):
    """자연어를 PubMed 검색 쿼리로 변환합니다."""

    try:
        result = await generate_search_query(request.query)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return NaturalQueryResponse(
            original_query=result["original_query"],
            pubmed_query=result["pubmed_query"],
            explanation=result["explanation"],
            keywords=result["keywords"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"쿼리 생성 중 오류 발생: {str(e)}")
