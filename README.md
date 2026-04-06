# Creator Outreach Platform

A platform for creator agencies to manage their roster, discover brand partnerships with AI, scout contacts via Apollo, draft personalized outreach emails, and push drafts to Gmail.

## Tech Stack

- **Backend**: Python / FastAPI / SQLAlchemy (async) / PostgreSQL / ARQ + Redis
- **Frontend**: React / TypeScript / Vite / Tailwind CSS / shadcn/ui
- **AI**: Google Gemini for creator enrichment, brand discovery, and email drafting
- **Integrations**: Apollo.io (contact scouting), Gmail API (draft creation)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### Local Development

1. Copy environment config:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

2. Start infrastructure (Postgres + Redis):
   ```bash
   docker-compose up db redis -d
   ```

3. Start the backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. Start the ARQ worker:
   ```bash
   cd backend
   arq app.workers.settings.WorkerSettings
   ```

5. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Full Docker Setup

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

## Project Structure

```
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── core/     # Auth, exceptions, shared deps
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic request/response schemas
│   │   ├── services/ # Business logic + integrations
│   │   ├── workers/  # ARQ background jobs
│   │   └── prompts/  # LLM prompt templates
│   ├── alembic/      # DB migrations
│   └── scripts/      # CLI utilities (seed, OAuth setup)
├── frontend/         # Vite + React SPA
│   └── src/
│       ├── api/      # API client functions
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── types/
└── docker-compose.yml
```
