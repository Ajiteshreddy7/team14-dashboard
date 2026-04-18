"""
components/ai_helpers.py
------------------------
Grounded AI building blocks used by the HUD FMR Rent Intelligence dashboard.

Exports:
  get_llm_client()        - OpenAI-compatible client from secrets/env
  chat(messages, ...)     - single call wrapper with error handling
  insight_card(...)       - AI "Explain this view" narrative on any df slice
  fairness_check(...)     - Salary Calculator verdict grounded in HUD data
  relocation_verdict(...) - Two-city recommendation grounded in HUD data
  nl_query_box(...)       - Natural-language -> safe pandas filter executor

All functions are defensive: if no API key is configured, they render a
graceful inline hint instead of crashing the dashboard.
"""

from __future__ import annotations

import os
import re
import json
import textwrap
from typing import Iterable, Optional

import pandas as pd
import streamlit as st

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


# ---- Canonical dashboard context (shared system prompt) ----
DASHBOARD_CONTEXT = textwrap.dedent("""
    You are "RentBot", an analyst embedded in the Team 14 HUD FMR Rent
    Intelligence Dashboard. You help HR compensation analysts, recruiters,
    and relocating employees interpret HUD Fair Market Rent (FMR) data.

    Canonical columns in the master dataframe (df):
      display_name       - "County, ST" or "City, ST"
      state_code         - 2-letter USPS code
      br0_fmr..br4_fmr   - FMR in USD for Studio-4BR
      median_income      - HUD Section 8 median household income ($)
      rent_burden_pct    - annual_gross_rent / median_income * 100
      burden_category    - "Affordable (<30%)" | "Moderate (30-50%)" | "Severe (>50%)"
      livability_score   - 0-100 composite (higher = better)
      rent_index         - 0-100 normalized vs. most expensive market

    Rules:
      1. Ground every claim in the SUMMARY rows you are given. Never
         invent a number or a place that is not in the summary.
      2. Be concise. Prefer 3-6 sentences, or 3-5 bullets when listing.
      3. Always name the metric behind any judgement
         (e.g., "Moderate burden because rent_burden_pct = 34%").
      4. If the data is insufficient, say so plainly.
""").strip()


# ---- Client factory ----
def get_llm_client():
    """Return an OpenAI-compatible client, or None if not configured."""
    if OpenAI is None:
        return None
    try:
        key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        base = st.secrets.get("OPENAI_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1"))
    except Exception:
        key = os.getenv("OPENAI_API_KEY", "")
        base = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
    if not key:
        return None
    return OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)


def _model() -> str:
    try:
        return st.secrets.get("CHATBOT_MODEL", os.getenv("CHATBOT_MODEL", "llama-3.3-70b-versatile"))
    except Exception:
        return os.getenv("CHATBOT_MODEL", "llama-3.3-70b-versatile")


def chat(messages: list, max_tokens: int = 400, temperature: float = 0.2) -> str:
    client = get_llm_client()
    if client is None:
        return "AI features are offline - OPENAI_API_KEY is not configured."
    try:
        resp = client.chat.completions.create(
            model=_model(),
            messages=[{"role": "system", "content": DASHBOARD_CONTEXT}, *messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"AI request failed: {e}"


# ---- 1. Insight Card (works on any chart / slice) ----
def _frame_summary(df: Optional[pd.DataFrame], cols: Optional[Iterable[str]] = None, n: int = 12) -> str:
    if df is None or df.empty:
        return "EMPTY DATAFRAME"
    view = df[[c for c in cols if c in df.columns]] if cols else df
    num = view.select_dtypes("number")
    desc = num.describe().round(2).to_string() if not num.empty else ""
    return (
        f"Shape: {view.shape}\n"
        f"Head:\n{view.head(n).to_string(index=False)}\n\n"
        f"Numeric summary:\n{desc}"
    )


def insight_card(
    section_title: str,
    df: Optional[pd.DataFrame],
    question: str,
    *,
    cols: Optional[Iterable[str]] = None,
    key: Optional[str] = None,
):
    """Render an 'AI insight - <section>' expander that narrates the given slice."""
    with st.expander(f"AI insight - {section_title}", expanded=False):
        if df is None or df.empty:
            st.info("Load data first to generate an insight.")
            return
        if st.button("Generate insight", key=key or f"insight_{section_title}"):
            with st.spinner("Analyzing..."):
                summary = _frame_summary(df, cols)
                user = (
                    f"Section: {section_title}\n"
                    f"Question: {question}\n\n"
                    f"DATA (authoritative - only use these rows/values):\n{summary}"
                )
                st.markdown(chat([{"role": "user", "content": user}], max_tokens=500))


# ---- 2. Salary Calculator fairness check ----
def fairness_check(
    location: str,
    bedroom_label: str,
    annual_salary: float,
    local_row,
):
    with st.expander("AI fairness check", expanded=True):
        if local_row is None:
            st.info("No HUD row available for this location - cannot run fairness check.")
            return
        if hasattr(local_row, "empty") and local_row.empty:
            st.info("No HUD row available for this location - cannot run fairness check.")
            return
        fmr_val = None
        try:
            fmr_val = local_row.get("br2_fmr", None)
        except Exception:
            fmr_val = None
        if fmr_val is None:
            try:
                fmr_series = local_row.filter(like="_fmr")
                fmr_val = float(fmr_series.iloc[0]) if len(fmr_series) else 0.0
            except Exception:
                fmr_val = 0.0
        facts = {
            "location": location,
            "bedroom": bedroom_label,
            "annual_salary": float(annual_salary),
            "fmr": float(fmr_val or 0),
            "median_income": float(local_row.get("median_income", 0) or 0),
            "rent_burden_pct": float(local_row.get("rent_burden_pct", 0) or 0),
            "burden_category": str(local_row.get("burden_category", "Unknown")),
        }
        user = (
            "Given this single-location HUD record and a proposed salary, say "
            "whether the offer is Affordable / Moderate / Severe relative to "
            "local rent burden, and give ONE actionable sentence.\n\n"
            f"FACTS: {json.dumps(facts)}"
        )
        st.markdown(chat([{"role": "user", "content": user}], max_tokens=250))


# ---- 3. Relocation verdict ----
def relocation_verdict(row_a, row_b, bedroom_label: str):
    with st.expander("AI relocation recommendation", expanded=True):
        if row_a is None or row_b is None:
            st.info("Pick two locations to get a recommendation.")
            return

        def pack(r):
            return {
                "name": r.get("display_name"),
                "state": r.get("state_code"),
                "fmr_2br": float(r.get("br2_fmr", 0) or 0),
                "median_income": float(r.get("median_income", 0) or 0),
                "rent_burden_pct": float(r.get("rent_burden_pct", 0) or 0),
                "burden_category": r.get("burden_category"),
                "livability_score": float(r.get("livability_score", 0) or 0),
            }

        user = (
            f"Compare these two locations for a {bedroom_label} relocation. "
            "Pick the better option OR say 'it depends' if trade-offs are close. "
            "Name the deciding metric.\n\n"
            f"A: {json.dumps(pack(row_a))}\nB: {json.dumps(pack(row_b))}"
        )
        st.markdown(chat([{"role": "user", "content": user}], max_tokens=280))


# ---- 4. Natural-language query (safe pandas filter) ----
_ALLOWED_COLS = {
    "display_name", "state_code",
    "br0_fmr", "br1_fmr", "br2_fmr", "br3_fmr", "br4_fmr",
    "median_income", "rent_burden_pct", "burden_category",
    "livability_score", "rent_index",
}
_ALLOWED_RE = re.compile(r'^[\s\w\.\(\)&|<>=!,"\'\-\+\*/%]+$')
STATE_NAME_TO_CODE = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}

def _replace_state_names_with_codes(question: str) -> str:
    q = question
    for name in sorted(STATE_NAME_TO_CODE.keys(), key=len, reverse=True):
        code = STATE_NAME_TO_CODE[name]
        q = re.sub(rf"\b{re.escape(name)}\b", code, q, flags=re.IGNORECASE)
    return q

def _safe_query(df: pd.DataFrame, expr: str) -> pd.DataFrame:
    if "__" in expr or not _ALLOWED_RE.match(expr):
        raise ValueError("Unsafe characters in query.")
    bare = re.sub(r'\"[^\"]*\"|\'[^\']*\'', '', expr)  # strip string literals
    referenced = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", bare))
    bad = referenced - _ALLOWED_COLS - {
        "and", "or", "not", "in", "True", "False",
        "str", "contains", "startswith", "endswith",
        "max", "min", "mean", "median", "sum", "abs",
        "round", "len", "upper", "lower",
    }
    if bad:
        raise ValueError(f"Unknown/forbidden identifiers: {sorted(bad)}")
    return df.query(expr, engine="python")


def nl_query_box(df: Optional[pd.DataFrame]):
    st.subheader("Ask the data in plain English")
    st.caption(
        'Examples: counties in Texas where br2_fmr < 1200 | '
        'counties in CA where median_income > 80000 | '
        'places with livability_score > 70 and rent_burden_pct < 30'
    )

    if df is None or df.empty:
        st.info("Load data first to query it.")
        return

    q = st.text_input("Your question", key="nl_query_input")
    if not q:
        return

    normalized_question = _replace_state_names_with_codes(q)

    with st.spinner("Translating..."):
        prompt = (
            "Translate the user's question into a SINGLE pandas DataFrame.query() expression "
            "using ONLY these columns: "
            + ", ".join(sorted(_ALLOWED_COLS))
            + ". Return ONLY the expression. No explanation. No code fences.\n\n"
            "Rules:\n"
            "- Use only these dataframe columns.\n"
            "- Use ==, !=, <, <=, >, >= for comparisons.\n"
            "- Use & for AND, | for OR, and ~ for NOT.\n"
          "- String values must be in double quotes.\n"
            '- For states, use state_code == "TX" style comparisons.\n'
            "- If the user mentions salary or income, map it to median_income.\n"
            "- If the user mentions affordable, use burden_category == \"Affordable (<30%)\".\n"
            "- If the user mentions moderate, use burden_category == \"Moderate (30-50%)\".\n"
            "- If the user mentions severe, use burden_category == \"Severe (>50%)\".\n"
            "- If the user mentions 0 bedroom or studio, use br0_fmr.\n"
            "- If the user mentions 1 bedroom, use br1_fmr.\n"
            "- If the user mentions 2 bedroom, use br2_fmr.\n"
            "- If the user mentions 3 bedroom, use br3_fmr.\n"
            "- If the user mentions 4 bedroom, use br4_fmr.\n"
            "- Counties or places refer to rows in the dataframe.\n"
            "- Do not invent columns.\n"
            "- Do NOT use method calls like .max(), .min(), .mean() inside the expression. "
            "Use numeric constants instead (e.g., rent_index > 90).\n\n"
            f"Question: {normalized_question}"
        )
        expr = chat([{"role": "user", "content": prompt}], max_tokens=120, temperature=0)

    expr = expr.strip().strip("`").replace("python", "").strip()
    st.code(expr, language="python")

    try:
        result = _safe_query(df, expr)
    except Exception as e:
        st.error(f"Could not run that query safely: {e}")
        return

    st.success(f"Matched {len(result):,} rows")
    st.dataframe(result.head(200), use_container_width=True)
