# Debate Platform Backend

A FastAPI backend for a debate platform that allows users to submit arguments on topics, with Claude AI synthesizing the debate into summaries.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
   - Copy `.env.example` to `.env`: `cp .env.example .env`
   - Edit `.env` and update with your actual database credentials and API keys:
     ```
     DB_HOST=localhost
     DB_PORT=5432
     DB_NAME=debate_platform
     DB_USER=postgres
     DB_PASSWORD=your_password
     ANTHROPIC_API_KEY=your_api_key_here
     ```
   
   **Note:** The `.env` file is gitignored and contains your actual credentials. The `.env.example` file contains sample/placeholder values.

3. Set up PostgreSQL database:
   - Install PostgreSQL if not already installed
   - Create a database: `CREATE DATABASE debate_platform;` (or use the name from your `.env` file)

4. Run the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/topics
Create a new debate topic.

**Request:**
```json
{
  "question": "Should we ban TikTok?",
  "created_by": "username"
}
```

**Response:**
```json
{
  "topic_id": 123,
  "question": "Should we ban TikTok?",
  "created_by": "username",
  "created_at": "2024-01-01T12:00:00"
}
```

### GET /api/topics
Get all topics with pro/con argument counts.

**Response:**
```json
[
  {
    "id": 123,
    "question": "Should we ban TikTok?",
    "pro_count": 5,
    "con_count": 7,
    "created_by": "username",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

### GET /api/topics/{topic_id}
Get a topic with all its arguments and analysis.

**Response:**
```json
{
  "id": 123,
  "question": "Should we ban TikTok?",
  "pro_arguments": [...],
  "con_arguments": [...],
  "overall_summary": null,
  "consensus_view": null,
  "timeline_view": null
}
```

### POST /api/topics/{topic_id}/arguments
Add an argument to a topic.

**Request:**
```json
{
  "side": "pro",
  "title": "Privacy concerns",
  "content": "TikTok collects too much user data...",
  "sources": "https://example.com",
  "author": "username"
}
```

**Response:**
```json
{
  "argument_id": 456
}
```

**Validation:** Topic must have at least 1 pro AND 1 con argument total.

### GET /api/topics/{topic_id}/arguments
Get arguments for a topic.

**Query Parameters:**
- `side`: Optional. Filter by 'pro', 'con', or 'both' (default)

**Response:**
Array of argument objects.

### POST /api/topics/{topic_id}/generate-summary
Generate AI summary using Claude. Requires at least one pro and one con argument.

**Response:**
```json
{
  "overall_summary": "...",
  "consensus_view": "...",
  "timeline_view": [
    {"period": "...", "description": "..."}
  ]
}
```

## Database

PostgreSQL database. The database connection is configured via environment variables:
- `DB_HOST` (default: localhost)
- `DB_PORT` (default: 5432)
- `DB_NAME` (default: debate_platform)
- `DB_USER` (default: postgres)
- `DB_PASSWORD` (default: postgres)

The database tables are automatically created when the application starts via `init_db()`.

### Schema

**topics:**
- id (SERIAL PRIMARY KEY)
- question (TEXT)
- created_by (TEXT)
- created_at (TIMESTAMP)
- overall_summary (TEXT, nullable)
- consensus_view (TEXT, nullable)
- timeline_view (TEXT/JSON, nullable)

**arguments:**
- id (SERIAL PRIMARY KEY)
- topic_id (INTEGER, FOREIGN KEY)
- side (TEXT: 'pro' or 'con')
- title (TEXT)
- content (TEXT)
- sources (TEXT, nullable)
- author (TEXT)
- created_at (TIMESTAMP)
- validity_score (INTEGER, nullable)
- validity_reasoning (TEXT, nullable)
- validity_checked_at (TIMESTAMP, nullable)
- key_urls (TEXT/JSON, nullable)
- votes (INTEGER, default: 0)

**argument_matches:**
- id (SERIAL PRIMARY KEY)
- topic_id (INTEGER, FOREIGN KEY)
- pro_id (INTEGER)
- con_id (INTEGER)
- reason (TEXT, nullable)
- created_at (TIMESTAMP)

## Error Handling

The API handles:
- Missing required fields (400 Bad Request)
- Invalid topic_id (404 Not Found)
- Invalid side values (400 Bad Request)
- Validation errors (400 Bad Request)
- Claude API failures (500 Internal Server Error)

