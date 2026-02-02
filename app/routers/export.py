from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import csv
from app.services.pubmed import search_pubmed, fetch_paper_details

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export/csv")
async def export_csv(
    query: str = Query(..., description="검색 키워드"),
    author: Optional[str] = Query(None, description="저자명"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY)"),
    max_results: int = Query(100, ge=1, le=500, description="최대 결과 수"),
):
    """검색 결과를 CSV 파일로 내보냅니다."""

    try:
        _, pmids = await search_pubmed(
            query=query,
            author=author,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=max_results,
        )

        papers = await fetch_paper_details(pmids) if pmids else []

        # CSV 생성
        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow([
            "PMID", "제목", "저자", "초록", "출판일", "저널명", "키워드"
        ])

        # 데이터
        for paper in papers:
            writer.writerow([
                paper.pmid,
                paper.title,
                "; ".join(paper.authors),
                paper.abstract,
                paper.pub_date,
                paper.journal,
                "; ".join(paper.keywords),
            ])

        output.seek(0)

        # UTF-8 BOM 추가 (Excel 호환)
        content = "\ufeff" + output.getvalue()

        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=pubmed_results_{query}.csv"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV 생성 중 오류 발생: {str(e)}")
