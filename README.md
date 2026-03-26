# OEM Alert

Enterprise vulnerability intelligence platform. Monitors 24+ OEM security advisories, provides real-time alerts, and manages security operations workflows.

## Services

| Service | Stack | Default Port |
|---|---|---|
| Dashboard | Streamlit | 8501 |
| API | FastAPI | 8000 |
| Frontend | Next.js 16 | 3000 |

## Setup

```bash
cp env.example .env
pip install -r requirements.txt
cd frontend && npm install
```

## Running

```bash
# Dashboard
streamlit run app.py

# API
uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev
```

## Deployment

- **Frontend:** Vercel (`cd frontend && vercel deploy`)
- **Dashboard + API:** Railway / Render (use `Procfile`)
- Set `FRONTEND_URL` in `.env` to your production frontend URL before deploying

## Environment Variables

Copy `env.example` to `.env` and fill in your credentials:
- `SUPABASE_*` — database and auth
- `STRIPE_*` — payments
- `SMTP_*` — email notifications
- `SLACK_BOT_TOKEN` — Slack alerts (optional)
