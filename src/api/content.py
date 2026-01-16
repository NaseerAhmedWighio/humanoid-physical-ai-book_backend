from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.course_module import CourseModule
from src.models.weekly_content import WeeklyContent
from sqlalchemy.orm import Session
from src.services.retrieving import retrieve

router = APIRouter()

@router.get("/modules")
async def get_modules(db: Session = Depends(get_db)):
    """
    Get all course modules
    """
    modules = db.query(CourseModule).all()
    return {"modules": [module.__dict__ for module in modules]}

@router.get("/modules/{module_id}")
async def get_module(module_id: str, db: Session = Depends(get_db)):
    """
    Get a specific course module
    """
    module = db.query(CourseModule).filter(CourseModule.id == UUID(module_id)).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.get("/weeks")
async def get_weeks(db: Session = Depends(get_db)):
    """
    Get all weekly content
    """
    weeks = db.query(WeeklyContent).all()
    return {"weeks": [week.__dict__ for week in weeks]}

@router.get("/weeks/{week_id}")
async def get_week(week_id: str, db: Session = Depends(get_db)):
    """
    Get a specific week's content
    """
    week = db.query(WeeklyContent).filter(WeeklyContent.id == UUID(week_id)).first()
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")
    return week

@router.post("/search")
async def search_content(query: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Search content using RAG functionality
    """
    results = retrieve(query, limit=limit)
    return {"query": query, "results": results, "limit": limit}

