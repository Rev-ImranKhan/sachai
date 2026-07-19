# SachAI — Sach Jaano, Sach Failao

AI-powered fake news & misinformation detector for India with multi-language support (Hindi / English / Hinglish).

## Stack
- FastAPI + SQLite
- Google Gemini (`gemini-2.0-flash`) via `google-genai`
- LangChain + ChromaDB (RAG over verified facts)
- JWT + bcrypt auth
- HTML / CSS / Vanilla JS frontend

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # add your GEMINI_API_KEY
python seed_facts.py              # populate ChromaDB + sample users/data
uvicorn main:app --reload
```

Open: http://localhost:8000

## Demo accounts
- `adil@demo.com` / `demo123`
- `arif@demo.com` / `demo123`

## Features
- Auth (register/login, JWT)
- Landing page with live counter & trust signals
- Dashboard with donut chart of verdicts
- Fact Checker: text / URL / WhatsApp forward
- Verdict: TRUE / FALSE / MISLEADING / PARTIALLY TRUE / UNVERIFIABLE
- Confidence meter, evidence for/against, spread risk
- History with filters & search
- Trending misinformation (curated)
- Community reports with up/down votes & AI auto-verdict
- RAG: ChromaDB seeded with 30 verified Indian fact-checks

## Notes
Without a `GEMINI_API_KEY`, the service falls back to a deterministic stub verdict so the UI is fully usable for demos.
