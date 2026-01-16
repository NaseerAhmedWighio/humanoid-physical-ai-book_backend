# Physical AI & Humanoid Robotics Textbook Backend

This is the backend API for the Physical AI & Humanoid Robotics textbook project, built with FastAPI and designed to support AI-native learning experiences.

## Features

- FastAPI-based REST API
- Qdrant vector database for RAG (Retrieval Augmented Generation)
- LLM integration with Gemini (Google AI)
- Content management and progress tracking
- Simulation integration (planned)
- Exercise and assessment system

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Qdrant vector database (cloud or local)
- API keys for LLM provider (Google Gemini, OpenAI, or Cohere)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd humanoid-ai-book/backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Update the `.env` file with your configuration:
   - Database URL
   - Qdrant configuration (URL and API key)
   - LLM provider API keys (Gemini, OpenAI, or Cohere)
   - JWT secret key for authentication

## Database Setup

1. Run database migrations:
```bash
alembic upgrade head
```

2. Populate the database with initial content:
```bash
python scripts/populate_db.py
```

## Running the Backend

Start the backend server:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

API documentation will be available at:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

## Content Upload to Qdrant

The system supports two methods for uploading content to Qdrant:

### Method 1: Sitemap-based Content Ingestion
This method fetches content from a sitemap URL and stores it in Qdrant:

```bash
python scripts/ingest_content.py
```

This script will:
1. Fetch URLs from the sitemap specified in `SITEMAP_URL` environment variable
2. Extract text content from each page
3. Chunk the text into manageable pieces
4. Create embeddings using Cohere
5. Store the embeddings in Qdrant

### Method 2: Local Markdown Files Processing
This method processes local markdown files from the `frontend/docs/` directory and uploads them to Qdrant:

```bash
python scripts/process_docs_to_qdrant.py
```

This script will:
1. Find all markdown files in the `frontend/docs/` directory and subdirectories
2. Convert markdown to plain text
3. Chunk the text into manageable pieces
4. Create embeddings using Cohere
5. Store the embeddings in Qdrant with proper metadata

Before running this script, ensure:
- Your markdown files are in the `frontend/docs/` directory
- Qdrant configuration is set in your `.env` file
- Cohere API key is configured in your `.env` file

## API Endpoints

### Content Management
- `GET /v1/content/modules` - Get all course modules
- `GET /v1/content/modules/{module_id}` - Get a specific module
- `GET /v1/content/weeks` - Get all weekly content
- `GET /v1/content/weeks/{week_id}` - Get specific week content
- `POST /v1/content/search` - Search content using RAG

### Chat & Interaction
- `POST /v1/chat/sessions` - Create a new chat session
- `POST /v1/chat/sessions/{session_id}/messages` - Send a message in a session
- `POST /v1/chat/ask-from-selection` - Ask about selected text

### Progress Tracking
- `GET /v1/progress/users/{user_id}/progress` - Get user progress
- `PUT /v1/progress/users/{user_id}/progress` - Update user progress

### Exercises
- `GET /v1/exercises` - Get exercises (with optional filters)
- `GET /v1/exercises/{exercise_id}` - Get specific exercise
- `POST /v1/exercises/{exercise_id}/submit` - Submit exercise answer
- `GET /v1/exercises/{exercise_id}/progress` - Get exercise progress

## Services Architecture

The backend uses three core services:

1. **LLM Service** (`src/services/llm_service.py`) - Handles communication with LLM providers
2. **Agent Service** (`src/services/agent.py`) - Manages AI agents for various tasks
3. **Retrieving Service** (`src/services/retrieving.py`) - Handles RAG functionality with Qdrant

## Environment Variables

Key environment variables in `.env`:

- `DATABASE_URL` - PostgreSQL database connection string
- `QDRANT_URL` - Qdrant vector database URL
- `QDRANT_API_KEY` - Qdrant API key (if using cloud)
- `LLM_PROVIDER` - LLM provider (gemini, openai)
- `GEMINI_API_KEY` - Google Gemini API key
- `COHERE_API_KEY` - Cohere API key for embeddings
- `JWT_SECRET_KEY` - Secret key for JWT tokens

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
# Using black for code formatting
pip install black
black .
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## Troubleshooting

1. **Qdrant Connection Issues**: Verify `QDRANT_URL` and `QDRANT_API_KEY` in your `.env` file
2. **LLM API Errors**: Check that your API keys are valid and have sufficient quota
3. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
4. **CORS Issues**: Update `ALLOWED_ORIGINS` in `.env` to include your frontend URL

## Production Deployment

For production deployment:
1. Use a production-ready database (not SQLite)
2. Set `APP_ENV=production` in `.env`
3. Use proper SSL certificates
4. Implement proper logging and monitoring
5. Set up proper authentication and authorization