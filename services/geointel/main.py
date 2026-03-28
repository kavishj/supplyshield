import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import (OFAC_SIMILARITY_THRESHOLD, OFAC_MAX_MATCHES,  # pyright: ignore[reportMissingImports]
                    NEWS_HIGH_MIN_HEADLINES, NEWS_MEDIUM_MIN_HEADLINES,
                    ADVERSE_NEWS_TERMS)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os, time, logging, json, requests
from rapidfuzz import process, fuzz
from newsapi import NewsApiClient
from dotenv import load_dotenv

SERPER_URL  = "https://google.serper.dev/search"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

load_dotenv(r"C:\Users\KAVISH\supplyshield_final\.env", override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geointel")

app = FastAPI(title="GeoIntelAgent", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SDN_COLUMNS = ["sdn_type","name","entity_type","program","title",
               "call_sign","vess_type","tonnage","grt",
               "vessel_flag","vessel_owner","remarks"]
_sdn_df = None
_sdn_names = None
_news_client = None

def get_sdn():
    global _sdn_df, _sdn_names
    if _sdn_df is not None:
        return _sdn_df, _sdn_names
    for p in [Path("/app/data/sdn.csv"), Path("../../data/sdn.csv"),
              Path("data/sdn.csv"), Path(r"C:\Users\KAVISH\supplyshield_final\data\sdn.csv")]:
        if p.exists():
            df = pd.read_csv(p, names=SDN_COLUMNS, header=None, dtype=str, on_bad_lines="skip")
            df["name"] = df["name"].fillna("").str.upper().str.strip()
            _sdn_df    = df
            _sdn_names = df["name"].tolist()
            logger.info(f"Loaded {len(df):,} SDN records from {p}")
            return _sdn_df, _sdn_names
    _sdn_df    = pd.DataFrame(columns=SDN_COLUMNS)
    _sdn_names = []
    return _sdn_df, _sdn_names

def get_news_client():
    global _news_client
    if _news_client is not None:
        return _news_client
    token = os.getenv("NEWSAPI_KEY", "")
    if not token:
        return None
    _news_client = NewsApiClient(api_key=token)
    return _news_client

def _serper_search(query: str, num: int = 5) -> list:
    key = os.getenv("SERPER_API_KEY", "").strip()
    if not key:
        return []
    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=10,
        )
        resp.raise_for_status()
        return [
            {"title": r.get("title", ""), "snippet": r.get("snippet", "")}
            for r in resp.json().get("organic", [])[:num]
        ]
    except Exception as e:
        logger.warning(f"Serper search failed for '{query}': {e}")
        return []


def _extract_shareholders_via_llm(company_name: str, snippets: list) -> list:
    """
    Call Groq LLM to extract shareholder names and ownership percentages
    from web search snippets.
    Returns list of {"name": str, "ownership_pct": float}
    """
    token = os.getenv("GROQ_API_KEY", "").strip()
    if not token or not snippets:
        return []

    combined = "\n\n".join(
        f"[{i+1}] {s['title']}\n{s['snippet']}"
        for i, s in enumerate(snippets)
        if s.get("snippet")
    )

    prompt = (
        f"You are a financial analyst. Extract the names and ownership percentages "
        f"of the major shareholders of '{company_name}' from the search snippets below.\n\n"
        f"{combined}\n\n"
        f"Return ONLY a valid JSON array (no markdown, no explanation) in this exact format:\n"
        f'[{{"name": "Shareholder Name", "ownership_pct": 25.0}}, ...]\n'
        f"Rules:\n"
        f"- Include only shareholders with a stated percentage.\n"
        f"- Use the numeric percentage value (e.g. 45.5 not '45.5%').\n"
        f"- If no shareholder data is found, return an empty array: []\n"
        f"- Do NOT include any text outside the JSON array."
    )

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": 0.0,
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        shareholders = json.loads(raw)
        if isinstance(shareholders, list):
            return [
                {"name": str(s["name"]).strip(), "ownership_pct": float(s["ownership_pct"])}
                for s in shareholders
                if "name" in s and "ownership_pct" in s
            ]
    except Exception as e:
        logger.warning(f"LLM shareholder extraction failed: {e}")
    return []


def _check_ofac_50_percent_rule(company_name: str, sdn_names: list, sdn_df) -> dict:
    """
    OFAC 50% Rule: if OFAC-blocked parties cumulatively own >= 50% of the company,
    the company itself is considered blocked.
    Returns a result dict with status, shareholders found, OFAC matches, cumulative %.
    """
    # Search for shareholding information
    queries = [
        f'"{company_name}" major shareholders ownership percentage stake',
        f'"{company_name}" ownership structure shareholding pattern investors',
    ]
    snippets = []
    for q in queries:
        snippets.extend(_serper_search(q, num=5))

    if not snippets:
        return {
            "status": "MANUAL_REVIEW",
            "note": "No shareholding data found via web search — manual verification recommended.",
            "shareholders": [],
            "ofac_shareholders": [],
            "cumulative_ofac_pct": 0.0,
        }

    shareholders = _extract_shareholders_via_llm(company_name, snippets)

    if not shareholders:
        return {
            "status": "MANUAL_REVIEW",
            "note": "Could not extract structured shareholder data — manual verification recommended.",
            "shareholders": [],
            "ofac_shareholders": [],
            "cumulative_ofac_pct": 0.0,
        }

    # Check each shareholder against OFAC SDN list
    ofac_shareholders = []
    cumulative_pct = 0.0

    for sh in shareholders:
        sh_name_upper = sh["name"].upper().strip()
        if not sdn_names:
            continue
        results = process.extract(
            sh_name_upper, sdn_names,
            scorer=fuzz.token_set_ratio,
            limit=1,
        )
        if results and results[0][1] >= OFAC_SIMILARITY_THRESHOLD:
            matched_name, similarity, idx = results[0]
            row = sdn_df.iloc[idx]
            ofac_shareholders.append({
                "shareholder_name":  sh["name"],
                "ownership_pct":     sh["ownership_pct"],
                "ofac_match":        matched_name,
                "similarity":        round(similarity, 1),
                "program":           row.get("program", ""),
            })
            cumulative_pct += sh["ownership_pct"]

    cumulative_pct = round(cumulative_pct, 2)

    if cumulative_pct >= 50.0:
        status = "BLOCKED"
        note = (
            f"OFAC 50% Rule triggered: OFAC-listed parties cumulatively hold "
            f"{cumulative_pct}% of {company_name}."
        )
    else:
        status = "CLEAR"
        note = (
            f"OFAC 50% Rule: OFAC-listed parties hold {cumulative_pct}% — below 50% threshold."
            if ofac_shareholders else
            f"OFAC 50% Rule: No shareholders matched OFAC SDN list."
        )

    return {
        "status":              status,
        "note":                note,
        "shareholders":        shareholders,
        "ofac_shareholders":   ofac_shareholders,
        "cumulative_ofac_pct": cumulative_pct,
    }


class ScreenRequest(BaseModel):
    company_name: str
    skip_news:    bool = False

@app.on_event("startup")
async def startup():
    get_sdn()

@app.get("/health")
def health():
    df, _ = get_sdn()
    return {
        "agent":              "GeoIntelAgent",
        "status":             "healthy",
        "sdn_records":        len(df),
        "newsapi_configured": bool(os.getenv("NEWSAPI_KEY", "")),
        "fuzzy_matching":     True,
    }

@app.post("/screen")
def screen(req: ScreenRequest):
    if not req.company_name.strip():
        raise HTTPException(status_code=400, detail="company_name is required")
    if len(req.company_name.strip()) > 200:
        raise HTTPException(status_code=400, detail="company_name exceeds 200 characters")

    start      = time.perf_counter()
    df, names  = get_sdn()
    term       = req.company_name.upper().strip()

    # ── OFAC Fuzzy Matching ───────────────────────────────────
    ofac_status    = "CLEAR"
    matched_entities = []
    match_count    = 0
    top_score      = 0

    if names:
        # rapidfuzz returns top 10 matches with similarity scores
        results = process.extract(term, names, scorer=fuzz.token_set_ratio, limit=OFAC_MAX_MATCHES)

        for matched_name, similarity, idx in results:
            if similarity >= OFAC_SIMILARITY_THRESHOLD:
                row = df.iloc[idx]
                matched_entities.append({
                    "name":       matched_name,
                    "type":       row["entity_type"],
                    "program":    row["program"],
                    "similarity": round(similarity, 1),
                })
                top_score = max(top_score, similarity)

        match_count = len(matched_entities)
        if match_count > 0:
            ofac_status = "SANCTIONED"

    # ── NewsAPI Live Search ───────────────────────────────────
    news_risk      = "NONE"
    news_headlines = []
    news_error     = None

    if not req.skip_news:
        try:
            client = get_news_client()
            if client:
                # Build dynamic query from config adverse terms (first 8 to stay within NewsAPI length limits)
                terms = " OR ".join(
                    f'"{t}"' if " " in t else t for t in ADVERSE_NEWS_TERMS[:8]
                )
                articles = client.get_everything(
                    q=f'"{req.company_name}" ({terms})',
                    language="en",
                    sort_by="relevancy",
                    page_size=5,
                )
                if articles["status"] == "ok":
                    for a in articles["articles"]:
                        headline = a.get("title", "")
                        if headline and headline != "[Removed]":
                            news_headlines.append(headline)

                if len(news_headlines) >= NEWS_HIGH_MIN_HEADLINES:
                    news_risk = "HIGH"
                elif len(news_headlines) >= NEWS_MEDIUM_MIN_HEADLINES:
                    news_risk = "MEDIUM"
                else:
                    news_risk = "LOW"
            else:
                news_error = "NewsAPI key not configured"

        except Exception as e:
            news_error = str(e)
            logger.warning(f"NewsAPI failed: {e}")

    # ── OFAC 50% Rule (Shareholding Check) ───────────────────────
    # Only run if the direct OFAC check is CLEAR — if it's already SANCTIONED
    # the gate will block anyway; no need to add latency.
    ofac_50_result = None
    if ofac_status == "CLEAR":
        try:
            ofac_50_result = _check_ofac_50_percent_rule(term, names, df)
            logger.info(
                f"OFAC 50% Rule for '{term}': {ofac_50_result['status']} "
                f"(cumulative OFAC pct: {ofac_50_result['cumulative_ofac_pct']}%)"
            )
        except Exception as e:
            logger.warning(f"OFAC 50% Rule check failed (non-fatal): {e}")
            ofac_50_result = {
                "status": "MANUAL_REVIEW",
                "note": f"50% rule check failed: {e}",
                "shareholders": [],
                "ofac_shareholders": [],
                "cumulative_ofac_pct": 0.0,
            }

    elapsed = round((time.perf_counter() - start) * 1000, 2)
    logger.info(f"Screened '{term}' -> OFAC:{ofac_status} News:{news_risk} in {elapsed}ms")

    return {
        "status":               ofac_status,
        "match_count":          match_count,
        "matched_entities":     matched_entities[:10],
        "top_similarity":       top_score,
        "records_searched":     len(df) if df is not None else 0,
        "news_risk":            news_risk,
        "news_headlines":       news_headlines,
        "news_error":           news_error,
        "ofac_50_percent_rule": ofac_50_result,
        "elapsed_ms":           elapsed,
    }