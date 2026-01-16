from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "humanoid-ai-textbook-api"}

@router.get("/")
async def root_health():
    return {"status": "API is running", "service": "humanoid-ai-textbook-api"}