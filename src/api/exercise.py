from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.exercise import Exercise

router = APIRouter()

@router.get("/exercises")
async def get_exercises(module_id: Optional[str] = None, week_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get exercises, optionally filtered by module or week
    """
    query = db.query(Exercise)

    if module_id:
        try:
            module_uuid = UUID(module_id)
            query = query.filter(Exercise.module_id == module_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid module ID format")
    elif week_id:
        try:
            week_uuid = UUID(week_id)
            query = query.filter(Exercise.week_id == week_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid week ID format")

    exercises = query.all()
    return {"exercises": [exercise.__dict__ for exercise in exercises]}

@router.get("/exercises/{exercise_id}")
async def get_exercise(exercise_id: str, db: Session = Depends(get_db)):
    """
    Get a specific exercise by ID
    """
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exercise ID format")

    exercise = db.query(Exercise).filter(Exercise.id == exercise_uuid).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise

@router.post("/exercises/{exercise_id}/submit")
async def submit_exercise(exercise_id: str, answer: str, user_id: str, db: Session = Depends(get_db)):
    """
    Submit an answer for an exercise
    """
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exercise ID format")

    # Check if exercise exists
    exercise = db.query(Exercise).filter(Exercise.id == exercise_uuid).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # For now, return a simple success response
    # In a real implementation, you would grade the answer and update progress
    return {
        "exercise_id": exercise_id,
        "user_id": user_id,
        "submitted_answer": answer,
        "success": True,
        "graded": False,  # Placeholder - actual grading would happen here
        "feedback": "Answer submitted successfully. Grading will be implemented in a future update."
    }

@router.get("/exercises/{exercise_id}/progress")
async def get_exercise_progress(exercise_id: str, user_id: str, db: Session = Depends(get_db)):
    """
    Get a user's progress on a specific exercise
    """
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exercise ID format")

    # For now, return a basic progress structure
    # In a real implementation, you would look up actual progress data
    return {
        "exercise_id": exercise_id,
        "user_id": user_id,
        "progress": {
            "status": "not_started",  # Default status
            "attempts": 0,
            "last_attempt": None,
            "completed": False
        }
    }