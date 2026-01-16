from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.student_progress import StudentProgress

router = APIRouter()

@router.get("/users/{user_id}/progress")
async def get_user_progress(user_id: str, db: Session = Depends(get_db)):
    """Get user's progress through the course"""
    try:
        # Try to parse as UUID, if it fails, return 404
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    progress_records = db.query(StudentProgress).filter(StudentProgress.user_id == user_uuid).all()
    # Return empty list if no progress records found, instead of raising 404
    return {"user_id": user_id, "progress_records": [record.__dict__ for record in progress_records]}

@router.put("/users/{user_id}/progress")
async def update_user_progress(
    user_id: str,
    module_id: str = None,
    week_id: str = None,
    exercise_id: str = None,
    status: str = "in_progress",
    score: float = None,
    db: Session = Depends(get_db)
):
    """Update user's progress"""
    try:
        # Try to parse as UUID, if it fails, return 400
        user_uuid = UUID(user_id)
        module_uuid = UUID(module_id) if module_id else None
        week_uuid = UUID(week_id) if week_id else None
        exercise_uuid = UUID(exercise_id) if exercise_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Create or update progress record
    progress = StudentProgress(
        user_id=user_uuid,
        module_id=module_uuid,
        week_id=week_uuid,
        exercise_id=exercise_uuid,
        status=status,
        score=score
    )

    db.add(progress)
    db.commit()
    db.refresh(progress)

    return {"user_id": user_id, "progress_id": str(progress.id), "updated": True}