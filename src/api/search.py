from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
from ..services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

# Initialize search service
search_service = SearchService()


@router.get("/")
async def search_endpoint(
    q: str,
    limit: Optional[int] = 10,
    offset: Optional[int] = 0
):
    """
    Search content with query parameters
    This endpoint provides consistent search functionality across the application
    """
    try:
        # Validate query parameter
        if not q or not q.strip():
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required and cannot be empty")

        # Validate limit parameter
        if limit and (limit < 1 or limit > 100):
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

        # Validate offset parameter
        if offset and offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be greater than or equal to 0")

        # Perform search using the search service
        try:
            results = await search_service.search_content(
                query=q.strip(),
                limit=min(limit, 100),  # Cap at 100 for performance
                offset=offset
            )
        except Exception as search_error:
            logger.error(f"Search service error: {str(search_error)}")
            # Return empty results with error flag instead of throwing exception
            return {
                "results": [],
                "total": 0,
                "query": q.strip(),
                "limit": min(limit, 100),
                "offset": offset,
                "error": "Search service temporarily unavailable"
            }

        return {
            "results": [
                {
                    "content_id": item.content_id,
                    "title": item.title,
                    "snippet": item.snippet,
                    "relevance_score": item.relevance_score
                }
                for item in results.results
            ],
            "total": results.total_results,
            "query": results.query,
            "limit": min(limit, 100),
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        # Return a safe fallback instead of throwing an exception
        return {
            "results": [],
            "total": 0,
            "query": q.strip() if q else "",
            "limit": min(limit or 10, 100),
            "offset": offset or 0,
            "error": "Search service is temporarily unavailable"
        }


@router.get("/health")
async def search_health():
    """
    Health check for search functionality
    """
    try:
        # Use the search service's health check method
        is_healthy = await search_service.health_check()
        if is_healthy:
            return {
                "status": "healthy",
                "search_service_available": True,
                "message": "Search service is operational"
            }
        else:
            return {
                "status": "unhealthy",
                "search_service_available": False,
                "message": "Search service is experiencing issues"
            }
    except Exception as e:
        logger.error(f"Search health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "search_service_available": False,
            "message": f"Search service health check failed: {str(e)}"
        }