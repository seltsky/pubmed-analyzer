from pydantic import BaseModel
from typing import Optional
from datetime import date


class Paper(BaseModel):
    pmid: str
    title: str
    authors: list[str]
    abstract: str
    pub_date: str
    journal: str
    keywords: list[str] = []
    pmc_id: str | None = None  # PMC ID (무료 전문 PDF 제공 시)
    citation_count: int | None = None  # 피인용 횟수 (iCite)


class SearchRequest(BaseModel):
    query: str
    author: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20


class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    papers: list[Paper]


class SummarizeRequest(BaseModel):
    pmids: list[str]
    language: str = "korean"


class SummaryResponse(BaseModel):
    summary: str
    pmids: list[str]


class KeywordAnalysis(BaseModel):
    keyword: str
    count: int


class TrendAnalysis(BaseModel):
    year: str
    count: int


class AuthorAnalysis(BaseModel):
    author: str
    count: int


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    pmids: list[str]
    message: str
    history: list[ChatMessage] = []
    language: str = "korean"


class ChatResponse(BaseModel):
    response: str
    pmids: list[str]
