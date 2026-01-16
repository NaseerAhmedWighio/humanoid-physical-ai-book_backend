"""
Script to populate the database with initial content for the Humanoid AI Textbook
"""
import asyncio
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import CourseModule, WeeklyContent
from datetime import datetime
import uuid

def get_db_session():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_sample_modules(db: Session):
    """Create sample course modules"""
    print("Creating sample course modules...")

    # Sample modules based on the spec
    modules_data = [
        {
            "title": "Introduction to ROS 2",
            "module_number": 1,
            "description": "Fundamentals of Robot Operating System 2 for humanoid robotics applications",
            "word_count": 4000,
            "estimated_duration_hours": 10.0,
            "learning_outcomes": [
                "Understand ROS 2 architecture and concepts",
                "Create ROS 2 nodes, topics, services, and actions",
                "Work with URDF for humanoid robot models"
            ]
        },
        {
            "title": "Simulation with Gazebo and Unity",
            "module_number": 2,
            "description": "Simulation environments for testing humanoid robots",
            "word_count": 4200,
            "estimated_duration_hours": 12.0,
            "learning_outcomes": [
                "Set up Gazebo simulation environments",
                "Create Unity scenes for robot simulation",
                "Implement physics-based robot control"
            ]
        },
        {
            "title": "NVIDIA Isaac for Humanoid Control",
            "module_number": 3,
            "description": "Using NVIDIA Isaac platform for advanced humanoid robotics",
            "word_count": 4500,
            "estimated_duration_hours": 14.0,
            "learning_outcomes": [
                "Implement perception systems using Isaac",
                "Develop control algorithms for humanoid robots",
                "Optimize performance with NVIDIA hardware"
            ]
        },
        {
            "title": "Vision Language Action (VLA) Models",
            "module_number": 4,
            "description": "Understanding and implementing VLA models for robot interaction",
            "word_count": 4800,
            "estimated_duration_hours": 16.0,
            "learning_outcomes": [
                "Understand VLA model architecture",
                "Implement vision-language integration",
                "Apply VLA models to humanoid tasks"
            ]
        }
    ]

    for module_data in modules_data:
        existing = db.query(CourseModule).filter(CourseModule.module_number == module_data["module_number"]).first()
        if not existing:
            module = CourseModule(**module_data)
            db.add(module)

    db.commit()
    print(f"Created {len(modules_data)} sample modules")

def create_sample_weekly_content(db: Session):
    """Create sample weekly content"""
    print("Creating sample weekly content...")

    # Get all modules to associate with weekly content
    modules = db.query(CourseModule).all()

    # Create 13 weeks of content
    weeks_data = []
    for week_num in range(1, 14):
        module_idx = (week_num - 1) // 4  # Each module covers about 3-4 weeks
        if module_idx >= len(modules):
            module_idx = len(modules) - 1

        week_data = {
            "week_number": week_num,
            "title": f"Week {week_num}: {modules[module_idx].title} - Topic {week_num}",
            "module_id": modules[module_idx].id,
            "subtopics": [f"Subtopic {i}" for i in range(1, 4)],  # 3 subtopics per week
            "content_path": f"frontend/docs/weeks/week-{week_num:02d}.md",
            "exercises_count": 3,
            "quizzes_count": 1,
            "case_studies_count": 1
        }
        weeks_data.append(week_data)

    for week_data in weeks_data:
        existing = db.query(WeeklyContent).filter(WeeklyContent.week_number == week_data["week_number"]).first()
        if not existing:
            week = WeeklyContent(**week_data)
            db.add(week)

    db.commit()
    print(f"Created {len(weeks_data)} sample weekly content entries")

def main():
    """Main function to populate the database"""
    print("Populating database with initial content...")

    # Get database session
    db_gen = get_db_session()
    db = next(db_gen)

    try:
        create_sample_modules(db)
        create_sample_weekly_content(db)
        print("Database populated successfully!")
    except Exception as e:
        print(f"Error populating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()