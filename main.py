import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

from database import db, init_db
from auth import (
    hash_password, verify_password, create_token,
    get_current_user, get_optional_user,
)
from gemini_service import analyze_claim

BASE = Path(__file__).parent
app = FastAPI(title="SachAI")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")

init_db()

@app.on_event("startup")
async def _auto_seed():
    import asyncio
    def _seed():
        try:
            from seed_facts import seed
            seed()
        except Exception as e:
            print(f"[startup] auto-seed skipped: {e}")
    await asyncio.to_thread(_seed)

TRENDING = {
    "Health": [
        {"claim": "Boiling neem leaves cures dengue", "debunk": "No clinical evidence; consult a doctor."},
        {"claim": "Vitamin D megadose prevents all infections", "debunk": "Excess can cause toxicity."},
    ],
    "Politics": [
        {"claim": "Voter list will be deleted if not re-verified in 7 days", "debunk": "ECI has issued no such notice."},
        {"claim": "New election rule bans social media on poll day", "debunk": "Only campaigning is restricted, not personal use."},
    ],
    "Technology": [
        {"claim": "WhatsApp is being shut down in India", "debunk": "No such announcement from Meta."},
        {"claim": "5G towers cause infertility", "debunk": "WHO & DoT confirm safe within limits."},
    ],
    "Religion": [
        {"claim": "Eclipse food becomes poisonous", "debunk": "AIIMS: no scientific basis."},
        {"claim": "Specific date is 'curse day' — avoid travel", "debunk": "No scientific evidence."},
    ],
    "Finance": [
        {"claim": "Rs 500 note being demonetised next month", "debunk": "RBI has issued no such notice."},
        {"claim": "Government giving Rs 10000 to all account holders", "debunk": "Phishing scam — never click."},
    ],
}


def render(request: Request, name: str, **ctx):
    user = get_optional_user(request)
    return templates.TemplateResponse(name, {"request": request, "user": user, **ctx})


# ---------- Pages ----------
@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return render(request, "index.html")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render(request, "login.html", error=None)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render(request, "register.html", error=None)


@app.get("/logout")
def logout():
    r = RedirectResponse("/", status_code=302)
    r.delete_cookie("access_token")
    return r


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: dict = Depends(get_current_user)):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM fact_checks WHERE user_id=? ORDER BY created_at DESC LIMIT 6",
            (user["id"],),
        ).fetchall()
        all_verdicts = conn.execute(
            "SELECT verdict, COUNT(*) c FROM fact_checks WHERE user_id=? GROUP BY verdict",
            (user["id"],),
        ).fetchall()
        community_count = conn.execute("SELECT COUNT(*) c FROM community_reports").fetchone()["c"]
        total = conn.execute("SELECT COUNT(*) c FROM fact_checks WHERE user_id=?", (user["id"],)).fetchone()["c"]
    breakdown = {r["verdict"]: r["c"] for r in all_verdicts}
    return render(
        request, "dashboard.html",
        recent=[dict(r) for r in rows],
        breakdown=breakdown,
        total=total,
        community_count=community_count,
        trending=TRENDING,
    )


@app.get("/fact-check", response_class=HTMLResponse)
def fact_check_page(request: Request, user: dict = Depends(get_current_user)):
    return render(request, "fact_check.html")


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request, user: dict = Depends(get_current_user)):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM fact_checks WHERE user_id=? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    return render(request, "history.html", checks=[dict(r) for r in rows])


@app.get("/result/{check_id}", response_class=HTMLResponse)
def result_detail(check_id: int, request: Request, user: dict = Depends(get_current_user)):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM fact_checks WHERE id=? AND user_id=?",
            (check_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(404)
    data = dict(row)
    data["analysis"] = json.loads(data["analysis_json"])
    return render(request, "result_detail.html", check=data)


@app.get("/trending", response_class=HTMLResponse)
def trending_page(request: Request):
    return render(request, "trending.html", trending=TRENDING)


@app.get("/community", response_class=HTMLResponse)
def community_page(request: Request):
    with db() as conn:
        rows = conn.execute(
            """SELECT cr.*, u.name AS reporter
               FROM community_reports cr JOIN users u ON u.id = cr.user_id
               ORDER BY (cr.upvotes - cr.downvotes) DESC, cr.created_at DESC"""
        ).fetchall()
        leaders = conn.execute(
            "SELECT name, checks_count FROM users ORDER BY checks_count DESC LIMIT 5"
        ).fetchall()
    return render(request, "community.html",
                  reports=[dict(r) for r in rows],
                  leaders=[dict(r) for r in leaders])


# ---------- Auth APIs ----------
@app.post("/api/register")
def api_register(name: str = Form(...), email: str = Form(...),
                 password: str = Form(...), language: str = Form("Both")):
    email = email.strip().lower()
    if len(password) < 6:
        raise HTTPException(400, "Password too short")
    with db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            raise HTTPException(400, "Email already registered")
        cur = conn.execute(
            "INSERT INTO users(name,email,password_hash,language) VALUES(?,?,?,?)",
            (name, email, hash_password(password), language),
        )
        uid = cur.lastrowid
    token = create_token(uid)
    r = RedirectResponse("/dashboard", status_code=302)
    r.set_cookie("access_token", token, httponly=True, samesite="lax")
    return r


@app.post("/api/login")
def api_login(email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        return templates.TemplateResponse("login.html",
                                          {"request": {}, "user": None,
                                           "error": "Invalid credentials"},
                                          status_code=401)
    token = create_token(row["id"])
    r = RedirectResponse("/dashboard", status_code=302)
    r.set_cookie("access_token", token, httponly=True, samesite="lax")
    return r


# ---------- Fact-check API ----------
def _fetch_url_text(url: str) -> str:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return url
        r = requests.get(url, timeout=8, headers={"User-Agent": "SachAI/1.0"})
        html = r.text
        import re
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
        og = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)', html, re.I)
        bits = []
        if title: bits.append(title.group(1).strip())
        if desc: bits.append(desc.group(1).strip())
        if og: bits.append(og.group(1).strip())
        return " — ".join(bits) or url
    except Exception:
        return url


@app.post("/api/check")
def api_check(payload: dict, user: dict = Depends(get_current_user)):
    text = (payload.get("text") or "").strip()
    typ = payload.get("type") or "text"
    if not text:
        raise HTTPException(400, "Empty input")
    claim = text
    if typ == "url":
        claim = _fetch_url_text(text)
    analysis = analyze_claim(claim, input_type=typ)
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO fact_checks(user_id,input_text,input_type,verdict,confidence,analysis_json) VALUES(?,?,?,?,?,?)",
            (user["id"], text, typ, analysis["verdict"], int(analysis.get("confidence", 70)),
             json.dumps(analysis)),
        )
        cid = cur.lastrowid
        conn.execute("UPDATE users SET checks_count = checks_count + 1 WHERE id=?", (user["id"],))
    return {"id": cid, "analysis": analysis}


@app.delete("/api/check/{cid}")
def api_delete_check(cid: int, user: dict = Depends(get_current_user)):
    with db() as conn:
        conn.execute("DELETE FROM fact_checks WHERE id=? AND user_id=?", (cid, user["id"]))
    return {"ok": True}


# ---------- Community ----------
@app.post("/api/community")
def api_community(payload: dict, user: dict = Depends(get_current_user)):
    claim = (payload.get("claim") or "").strip()
    if not claim:
        raise HTTPException(400, "Empty claim")
    analysis = analyze_claim(claim, input_type="text")
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO community_reports(user_id,claim_text,ai_verdict) VALUES(?,?,?)",
            (user["id"], claim, analysis["verdict"]),
        )
        rid = cur.lastrowid
    return {"id": rid, "verdict": analysis["verdict"]}


@app.post("/api/community/{rid}/vote")
def api_community_vote(rid: int, payload: dict, user: dict = Depends(get_current_user)):
    direction = payload.get("dir")
    field = "upvotes" if direction == "up" else "downvotes"
    with db() as conn:
        conn.execute(f"UPDATE community_reports SET {field} = {field} + 1 WHERE id=?", (rid,))
        row = conn.execute("SELECT upvotes, downvotes FROM community_reports WHERE id=?", (rid,)).fetchone()
    return dict(row) if row else {}
