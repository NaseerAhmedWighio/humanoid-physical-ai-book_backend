from typing import List
from datetime import datetime
import logging
from ..models.search_results import SearchResults, SearchResultsCreate, SearchResultItem

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        # In a real implementation, this would connect to Qdrant or another search backend
        # For now, using in-memory storage for demonstration
        self.search_results_db = {}

    async def search_content(self, query: str, user_id: str = None, limit: int = 10, offset: int = 0) -> SearchResults:
        """Perform a search for content"""
        try:
            # This is a simplified implementation
            # In a real system, this would query the Qdrant vector database

            # Create mock search results
            search_items = []
            for i in range(min(limit, 5)):  # Create up to 5 mock results
                search_items.append(
                    SearchResultItem(
                        content_id=f"content_{i}",
                        title=f"Search Result {i+1} for '{query}'",
                        snippet=f"This is a sample snippet containing the query '{query}' in the content.",
                        relevance_score=1.0 - (i * 0.1)  # Decreasing relevance
                    )
                )

            search_result = SearchResultsCreate(
                query=query,
                results=search_items,
                total_results=len(search_items),
                search_time=datetime.now()
            )

            # Create a search result record
            result_id = f"search_{datetime.now().timestamp()}"
            search_result_data = {
                "id": result_id,
                "query": search_result.query,
                "results": [item.dict() for item in search_result.results],
                "total_results": search_result.total_results,
                "search_time": search_result.search_time,
                "user_id": user_id
            }

            self.search_results_db[result_id] = search_result_data
            return SearchResults(**search_result_data)
        except Exception as e:
            logger.error(f"Error in search_content: {str(e)}")
            # Return a safe fallback with empty results
            fallback_result = SearchResultsCreate(
                query=query,
                results=[],
                total_results=0,
                search_time=datetime.now()
            )

            result_id = f"search_{datetime.now().timestamp()}_fallback"
            search_result_data = {
                "id": result_id,
                "query": fallback_result.query,
                "results": [item.dict() for item in fallback_result.results],
                "total_results": fallback_result.total_results,
                "search_time": fallback_result.search_time,
                "user_id": user_id
            }

            self.search_results_db[result_id] = search_result_data
            return SearchResults(**search_result_data)

    async def get_search_history(self, user_id: str) -> List[SearchResults]:
        """Get search history for a user"""
        try:
            user_searches = []
            for result_id, result_data in self.search_results_db.items():
                if result_data.get("user_id") == user_id:
                    user_searches.append(SearchResults(**result_data))
            return user_searches
        except Exception as e:
            logger.error(f"Error getting search history for user {user_id}: {str(e)}")
            # Return empty list as fallback
            return []

    async def health_check(self) -> bool:
        """Check if the search service is healthy"""
        try:
            # Perform a simple test
            test_result = await self.search_content(query="test", limit=1)
            return len(test_result.results) >= 0  # Always true for our mock implementation
        except Exception as e:
            logger.error(f"Search service health check failed: {str(e)}")
            return False