# Debately

A fact-checked debate platform that uses Claude AI to synthesize arguments, verify claims, and provide evidence-based analysis. Built for the Claude Builders Hackathon 2025.

## Features

- 🤖 **AI-Powered Synthesis** - Claude Sonnet 4 generates comprehensive debate summaries, consensus views, and timelines
- ✅ **Automatic Fact-Checking** - Claude Haiku + Tavily verify arguments and assign 1-5 star validity scores
- 🎯 **Relevance Filtering** - AI automatically rejects irrelevant arguments (no spam or off-topic content)
- 📊 **Evidence-Based Scoring** - Validity scores based on high-quality sources (relevance score > 0.5)
- 👍 **Voting System** - Users can upvote/downvote arguments
- 🔗 **Argument Matching** - AI identifies which pro arguments directly rebut con arguments
- 📈 **Topic Metrics** - View average validity scores, controversy levels, and argument counts

## Tech Stack

**Backend:**
- FastAPI (async Python framework)
- PostgreSQL
- Claude Sonnet 4 (synthesis, matching)
- Claude Haiku (fact-checking)
- Tavily API (evidence search)

**Frontend:**
- Next.js 16 (React framework)
- TypeScript
- Tailwind CSS
- Shadcn/ui components

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Anthropic API key
- Tavily API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="your_anthropic_key"
$env:TAVILY_API_KEY="your_tavily_key"

# Linux/Mac
export ANTHROPIC_API_KEY="your_anthropic_key"
export TAVILY_API_KEY="your_tavily_key"
```

4. Run the server:
```bash
uvicorn main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Usage

1. **Create a Debate** - Click "Start a Debate" and enter a question
2. **Add Arguments** - Submit pro and con arguments with sources
3. **Automatic Verification** - Arguments are automatically fact-checked on submission
4. **View Analysis** - Claude generates summaries, consensus views, and timelines
5. **Vote** - Upvote or downvote arguments to show support

## Sample Data

Create sample debates with varied argument quality:

```bash
cd backend
python create_sample_debates.py
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── routes/       # API endpoints
│   ├── database.py   # Database operations
│   ├── claude_service.py  # Sonnet 4 integration
│   └── fact_checker.py    # Haiku fact-checking
└── frontend/         # Next.js frontend
    ├── app/          # Pages and components
    └── src/          # API client
```

## Key Features Explained

### Multi-Model AI Strategy
- **Claude Sonnet 4**: Used for debate synthesis and argument matching (superior reasoning)
- **Claude Haiku**: Used for fact-checking (10x cheaper, 2-3x faster)

### Fact-Checking Pipeline
1. Extract verifiable claim from argument
2. Search for evidence using Tavily (filters sources with score > 0.5)
3. Analyze evidence and assign 1-5 star validity score

### Automatic Relevance Checking
Arguments are automatically checked for relevance before saving. Irrelevant arguments (opinions, spam, off-topic) are rejected with clear reasoning.

## License

Built for Claude Builders Hackathon 2025
