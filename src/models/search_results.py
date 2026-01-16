from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SearchResultItem(BaseModel):
    content_id: str
    title: str
    snippet: str
    relevance_score: float


class SearchResultsBase(BaseModel):
    query: str
    results: List[SearchResultItem] = []
    total_results: int = 0


class SearchResultsCreate(SearchResultsBase):
    search_time: datetime = datetime.now()


class SearchResults(SearchResultsBase):
    id: str
    search_time: datetime
    user_id: Optional[str] = None

    class Config:
        from_attributes = True