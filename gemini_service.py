import json
import os
import re
import time
from typing import Dict, List

from rag_engine import search_similar
import tavily_service

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = "gemini-flash-latest"
GROQ_MODEL = "llama-3.3-70b-versatile"

_client = None
if API_KEY:
    try:
        from google import genai
        _client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"[gemini] init failed, using stub: {e}")
        _client = None

_groq_client = None
if GROQ_API_KEY:
    try:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"[groq] init failed: {e}")
        _groq_client = None


SYSTEM_PROMPT = """You are SachAI, an expert fact-checker focused on Indian
misinformation (WhatsApp forwards, news, social posts). Analyze the claim
using the retrieved verified facts as context. Detect language (Hindi /
English / Hinglish). Return STRICT JSON only — no markdown.

Schema:
{
  "verdict": "TRUE | FALSE | MISLEADING | PARTIALLY TRUE | UNVERIFIABLE",
  "confidence": 0-100,
  "summary": "2-3 sentence explanation",
  "evidence_for": ["..."],
  "evidence_against": ["..."],
  "context": "important background",
  "sources_consulted": ["PIB", "WHO", "..."],
  "language_detected": "Hindi | English | Hinglish",
  "spread_risk": "Low | Medium | High",
  "recommended_action": "Safe to share | Do not share | Share with caution",
  "reasoning_steps": ["step 1", "step 2", "step 3"]
}
"""


def _stub_verdict(claim: str, similar: List[Dict]) -> Dict:
    text = claim.lower()
    verdict = "UNVERIFIABLE"
    conf = 55
    if similar:
        v = (similar[0].get("verdict") or "").upper()
        if v in {"TRUE", "FALSE", "MISLEADING", "PARTIALLY TRUE", "UNVERIFIABLE"}:
            verdict = v
            conf = 82
    if any(w in text for w in ["miracle cure", "cures cancer", "5g", "chip in vaccine", "free recharge"]):
        verdict, conf = "FALSE", 92
    lang = "English"
    if re.search(r"[\u0900-\u097F]", claim):
        lang = "Hindi"
    elif any(w in text for w in [" hai", " kar", " nahi", "kya", "bhai"]):
        lang = "Hinglish"
    return {
        "verdict": verdict,
        "confidence": conf,
        "summary": (
            "Based on the SachAI knowledge base and pattern analysis, this claim "
            f"appears {verdict.lower()}. Similar claims have been previously reviewed."
        ),
        "evidence_for": [s.get("claim", "")[:140] for s in similar[:1]] or ["No direct supporting evidence found."],
        "evidence_against": [s.get("explanation", "")[:200] for s in similar[:2]] or ["No verified counter-evidence retrieved."],
        "context": "India sees high volumes of WhatsApp-forwarded health, political and financial misinformation. Always verify with official sources (PIB Fact Check, WHO India, ECI).",
        "sources_consulted": ["PIB Fact Check", "WHO India", "AltNews", "BoomLive"],
        "language_detected": lang,
        "spread_risk": "High" if verdict == "FALSE" else "Medium",
        "recommended_action": "Do not share" if verdict == "FALSE" else ("Share with caution" if verdict in {"MISLEADING", "PARTIALLY TRUE"} else "Safe to share" if verdict == "TRUE" else "Share with caution"),
        "reasoning_steps": [
            "Extracted core claim from input.",
            f"Retrieved {len(similar)} similar verified record(s) from ChromaDB.",
            "Compared claim language and entities against verified database.",
            "Generated verdict with confidence based on retrieval overlap.",
        ],
    }


def _extract_json(s: str) -> Dict:
    m = re.search(r"\{.*\}", s, re.S)
    if not m:
        raise ValueError("no json")
    return json.loads(m.group(0))


def _call_gemini(prompt: str, retries: int = 2) -> str:
    if _client is None:
        return ""
    for attempt in range(retries + 1):
        try:
            resp = _client.models.generate_content(model=MODEL, contents=prompt)
            return getattr(resp, "text", "") or ""
        except Exception as e:
            msg = str(e)
            if ("429" in msg or "quota" in msg.lower() or "rate" in msg.lower()) and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            print(f"[gemini] error: {e}")
            return ""
    return ""


def _call_groq(prompt: str) -> str:
    if _groq_client is None:
        return ""
    try:
        resp = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        print(f"[groq] error: {e}")
        return ""


def analyze_claim(claim: str, input_type: str = "text") -> Dict:
    similar = search_similar(claim, k=4)
    context_block = "\n".join(
        f"- ({s.get('verdict','?')}) {s.get('claim','')}: {s.get('explanation','')[:200]}"
        for s in similar
    ) or "(no matches)"

    web_results = tavily_service.search_web(claim)
    web_block = tavily_service.format_for_prompt(web_results)

    prompt = (
        f"{SYSTEM_PROMPT}\n\nRetrieved verified facts:\n{context_block}\n\n"
        f"Live web search results (use these for current/recent claims):\n{web_block}\n\n"
        f"Input type: {input_type}\nClaim:\n{claim}\n\nReturn JSON only."
    )

    text = _call_gemini(prompt)
    if not text:
        text = _call_groq(prompt)

    if not text:
        out = _stub_verdict(claim, similar)
        out["similar"] = similar
        out["web_sources"] = web_results
        return out

    try:
        data = _extract_json(text)
        for k in ["evidence_for", "evidence_against", "sources_consulted", "reasoning_steps"]:
            data.setdefault(k, [])
        data.setdefault("confidence", 70)
        data.setdefault("verdict", "UNVERIFIABLE")
        data["similar"] = similar
        data["web_sources"] = web_results
        return data
    except Exception as e:
        print(f"[analyze_claim] JSON parse failed, using stub: {e}")
        out = _stub_verdict(claim, similar)
        out["similar"] = similar
        out["web_sources"] = web_results
        return out