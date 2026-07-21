# 🛡️ SachAI — AI-Powered Fact-Checking for Indian Misinformation
> A RAG + live-search fact-checking assistant that verifies WhatsApp forwards, news claims, and viral posts in Hindi, English, or Hinglish — grounded in retrieved evidence, not LLM guesswork.
>
> **🔗 Live Demo:** https://sachai-m0p6.onrender.com
> **📂 GitHub:** https://github.com/Rev-ImranKhan/sachai

## 🎯 Overview
India sees some of the highest volumes of WhatsApp-forwarded misinformation in the world — health myths, political rumors, financial scams — often spreading faster than they can be debunked. SachAI lets users paste a claim, URL, or forwarded message and get back a grounded verdict (TRUE / FALSE / MISLEADING / UNVERIFIABLE) with a confidence score, reasoning, and **live web sources**, not just an LLM's opinion.

## 🧠 Why This Project Matters
This project demonstrates practical **retrieval-grounded verification engineering**:
- **RAG over a verified-facts knowledge base** — claims are compared against a curated ChromaDB store of previously fact-checked claims before generation
- **Live web grounding** — Tavily search pulls real, current sources so verdicts aren't limited to the model's training cutoff
- **Dual-LLM resilience** — Gemini primary, Groq automatic fallback, with a deterministic stub verdict as a last resort so the app never hard-fails
- **Civic tech applied to information integrity** — using AI to slow the spread of misinformation rather than accelerate it

## ✨ Key Features
| Feature | Description |
|---|---|
| ✅ AI Verdict Engine | TRUE / FALSE / MISLEADING / PARTIALLY TRUE / UNVERIFIABLE with confidence score |
| 🌐 Live Web Sources | Tavily-powered real-time search grounds verdicts in current sources with clickable links |
| 📚 RAG Knowledge Base | ChromaDB-backed store of previously verified claims informs every new check |
| 📝 Multi-Input | Accepts plain text, URLs (auto-scraped), and WhatsApp forward pastes |
| 👥 Community Reports | Users submit and upvote/downvote claims flagged by the community |
| 📊 Personal Dashboard | Verdict breakdown, history, and a leaderboard of active fact-checkers |
| 🔁 Dual-LLM Fallback | Gemini primary → Groq fallback → stub verdict, so it always responds |

## 🧠 AI/RAG Architecture
| Component | Role |
|---|---|
| **Gemini (`gemini-flash-latest`)** | Primary LLM — claim analysis, verdict generation, reasoning steps |
| **Groq (`llama-3.3-70b-versatile`)** | Automatic fallback when Gemini is rate-limited or unavailable |
| **Tavily API** | Live web search — grounds verdicts in current, real sources beyond the model's training data |
| **ChromaDB** | Vector store of previously verified claims for retrieval-augmented context |
| **google-genai SDK** | Modern Google GenAI SDK for Gemini calls |

## 🛠️ Tech Stack
**Backend:** Python, FastAPI, Uvicorn, Jinja2
**AI:** Google Gemini, Groq, Tavily (live search), ChromaDB (vector search)
**Auth:** JWT (python-jose), Passlib/bcrypt
**Database:** SQLite
**Frontend:** HTML, CSS, Vanilla JS

## 📂 Project Structure
```
sachai/
├── main.py                 # FastAPI app, routes, startup seeding
├── gemini_service.py       # Gemini + Groq LLM orchestration, verdict schema
├── tavily_service.py        # Live web search integration
├── rag_engine.py             # ChromaDB retrieval of similar verified claims
├── auth.py                    # JWT auth, password hashing
├── database.py                 # SQLite connection/schema
├── seed_facts.py                # Verified facts + demo user seed data
├── templates/                     # Jinja2 HTML templates
└── static/                         # CSS, JS
```

## 🚀 Getting Started
### 1. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```
**Note:** ChromaDB on newer Python versions requires:
```bash
pip install chromadb --only-binary :all:
```

### 2. Configure Environment
Create a `.env` file in the root directory with:
```
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
JWT_SECRET=your_random_secret_here
```

### 3. Run the App
```bash
uvicorn main:app --reload
```
Visit: http://localhost:8000

**Demo login:** `adil@demo.com` / `demo123`

## 📌 Roadmap / Future Improvements
- [ ] Browser extension for one-click fact-checking on any page
- [ ] Image/screenshot OCR for checking forwarded images directly
- [ ] Regional language expansion beyond Hindi/English
- [ ] Shareable verdict cards for WhatsApp

## 👤 About the Developer
Built by **Imran Khan** — BCA final-year student specializing in **Applied AI Engineering** and **RAG systems**, focused on building AI tools that improve access to reliable information for Indian users.

📫 Open to **AI Solution Developer** / **Applied AI Engineer** roles.
🔗 [GitHub](https://github.com/Rev-ImranKhan)
