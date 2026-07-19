"""Lightweight RAG over ChromaDB. Falls back to a pure-Python TF/keyword
retriever if ChromaDB / embeddings are unavailable, so the app always runs."""
import json
import os
import re
from pathlib import Path
from typing import List, Dict

CHROMA_DIR = str(Path(__file__).parent / "chroma_db")
FACTS_JSON = Path(__file__).parent / "chroma_db" / "facts.json"

_collection = None
_use_chroma = False


def _try_init_chroma():
    global _collection, _use_chroma
    try:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
        _collection = client.get_or_create_collection("sachai_facts")
        _use_chroma = True
    except Exception as e:
        print(f"[rag] ChromaDB unavailable, using JSON fallback: {e}")
        _use_chroma = False


_try_init_chroma()


def add_facts(facts: List[Dict]):
    """facts: list of {claim, verdict, explanation, date, category}"""
    FACTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    FACTS_JSON.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    if _use_chroma and _collection is not None:
        try:
            ids = [f"fact_{i}" for i in range(len(facts))]
            docs = [f["claim"] + " — " + f["explanation"] for f in facts]
            metas = [{k: v for k, v in f.items() if k != "claim"} | {"claim": f["claim"]} for f in facts]
            try:
                _collection.delete(ids=ids)
            except Exception:
                pass
            _collection.add(ids=ids, documents=docs, metadatas=metas)
        except Exception as e:
            print(f"[rag] add to chroma failed: {e}")


def _load_json_facts() -> List[Dict]:
    if FACTS_JSON.exists():
        try:
            return json.loads(FACTS_JSON.read_text())
        except Exception:
            return []
    return []


def _tokenize(s: str):
    return set(re.findall(r"[a-zA-Z\u0900-\u097F]+", (s or "").lower()))


def search_similar(query: str, k: int = 4) -> List[Dict]:
    if _use_chroma and _collection is not None:
        try:
            res = _collection.query(query_texts=[query], n_results=k)
            out = []
            for doc, meta in zip(res.get("documents", [[]])[0], res.get("metadatas", [[]])[0]):
                m = dict(meta or {})
                m["snippet"] = doc
                out.append(m)
            if out:
                return out
        except Exception as e:
            print(f"[rag] query failed, falling back: {e}")
    facts = _load_json_facts()
    qt = _tokenize(query)
    scored = []
    for f in facts:
        ft = _tokenize(f.get("claim", "") + " " + f.get("explanation", ""))
        score = len(qt & ft)
        if score:
            scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:k]]
