from collections import Counter
from app.models.schemas import Paper, KeywordAnalysis, TrendAnalysis, AuthorAnalysis


def analyze_keywords(papers: list[Paper], top_n: int = 20) -> list[KeywordAnalysis]:
    """논문 목록에서 키워드 빈도를 분석합니다."""

    all_keywords = []
    for paper in papers:
        all_keywords.extend(paper.keywords)

    # 키워드 빈도 계산
    keyword_counts = Counter(all_keywords)
    top_keywords = keyword_counts.most_common(top_n)

    return [
        KeywordAnalysis(keyword=kw, count=count)
        for kw, count in top_keywords
    ]


def analyze_trends(papers: list[Paper]) -> list[TrendAnalysis]:
    """연도별 논문 수를 분석합니다."""

    year_counts = Counter()
    for paper in papers:
        if paper.pub_date:
            # 연도만 추출 (YYYY-MM-DD 또는 YYYY-MM 또는 YYYY)
            year = paper.pub_date.split("-")[0]
            if year.isdigit():
                year_counts[year] += 1

    # 연도순 정렬
    sorted_years = sorted(year_counts.items(), key=lambda x: x[0])

    return [
        TrendAnalysis(year=year, count=count)
        for year, count in sorted_years
    ]


def analyze_authors(papers: list[Paper], top_n: int = 20) -> list[AuthorAnalysis]:
    """저자별 논문 수를 분석합니다."""

    all_authors = []
    for paper in papers:
        all_authors.extend(paper.authors)

    # 저자 빈도 계산
    author_counts = Counter(all_authors)
    top_authors = author_counts.most_common(top_n)

    return [
        AuthorAnalysis(author=author, count=count)
        for author, count in top_authors
    ]
