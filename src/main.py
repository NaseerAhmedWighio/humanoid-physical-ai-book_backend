from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Physical AI & Humanoid Robotics Textbook API",
    description="Backend API for the AI-native textbook website",
    version="0.1.0"
)

# Add CORS middleware for frontend communication
# Get allowed origins from environment variable, fallback to wildcard for development
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")  # Use the correct spelling from .env
if allowed_origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Physical AI & Humanoid Robotics Textbook API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include API routes
from .api import content, chat, progress, exercise, auth, better_auth, translation
app.include_router(content.router, prefix="/v1/content", tags=["content"])
app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
app.include_router(progress.router, prefix="/v1/progress", tags=["progress"])
app.include_router(exercise.router, prefix="/v1/exercises", tags=["exercises"])
app.include_router(auth.router)
app.include_router(better_auth.router)
app.include_router(translation.router, prefix="/v1/translation", tags=["translation"])