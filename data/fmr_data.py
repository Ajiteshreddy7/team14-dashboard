"""
data/fmr_data.py
----------------
All HUD API calls for FMR and Income Limits data.
Caches results to CSV so we don't hammer the API on every rerun.

Endpoints used:
  GET /fmr/listStates
  GET /fmr/statedata/{state_code}?year=YYYY
  GET /il/data/{fips_code}?year=YYYY
"""

import os
import time
import requests
import numpy as np
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL  = "https://www.huduser.gov/hudapi/public"
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
FMR_YEAR  = "2025"

TREND_YEARS = ["2021", "2022", "2023", "2024", "2025"]

VALID_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
]

os.makedirs(CACHE_DIR, exist_ok=True)

# ── Token (set by app.py via fmr_module.API_TOKEN = token) ───────────────────
API_TOKEN = ""

# ── Internal helpers ──────────────────────────────────────────────────────────

def _headers():
    tok = API_TOKEN or os.environ.get("HUD_API_TOKEN", "")
    if not tok:
        raise ValueError("HUD_API_TOKEN is not set.")
    return {"Authorization": f"Bearer {tok}"}


def _get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    for attempt in range(3):
        try:
            r = requests.get(url, headers=_headers(), params=params, timeout=20)
            if r.status_code == 429:
                wait = 30 * (attempt + 1)
                print(f"[HUD API] Rate limited on {endpoint}, waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            print(f"[HUD API] HTTP {r.status_code} on {endpoint}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[HUD API] Error on {endpoint}: {e}")
            return None
    print(f"[HUD API] Failed after 3 attempts on {endpoint}")
    return None


def _cache_path(name):
    return os.path.join(CACHE_DIR, f"{name}.csv")


def _load_cache(name):
    path = _cache_path(name)
    if os.path.exists(path):
        return pd.read_csv(path, dtype={"fips_code": str, "fips5": str})
    return None


def _save_cache(df, name):
    df.to_csv(_cache_path(name), index=False)


# ── States ────────────────────────────────────────────────────────────────────

def get_states():
    cached = _load_cache("states")
    if cached is not None:
        return cached

    data = _get("fmr/listStates")
    if not data:
        return pd.DataFrame()

    records = data if isinstance(data, list) else data.get("data", data)
    df = pd.DataFrame(records)
    df = df[df["state_code"].isin(VALID_STATES)].reset_index(drop=True)
    _save_cache(df, "states")
    return df


# ── FMR ───────────────────────────────────────────────────────────────────────

def _fetch_fmr_state(state_code, year=FMR_YEAR):
    data = _get(f"fmr/statedata/{state_code}", params={"year": year})
    if not data or "data" not in data:
        return []

    rows = []
    for c in data["data"].get("counties", []):
        rows.append({
            "state_code":   state_code,
            "state_name":   c.get("statename", ""),
            "county_name":  c.get("county_name", ""),
            "town_name":    c.get("town_name", ""),
            "fips_code":    str(c.get("fips_code", "")),
            "metro_name":   c.get("metro_name", ""),
            "metro_status": str(c.get("metro_status", "0")),
            "br0_fmr":      float(c.get("Efficiency", 0) or 0),
            "br1_fmr":      float(c.get("One-Bedroom", 0) or 0),
            "br2_fmr":      float(c.get("Two-Bedroom", 0) or 0),
            "br3_fmr":      float(c.get("Three-Bedroom", 0) or 0),
            "br4_fmr":      float(c.get("Four-Bedroom", 0) or 0),
            "year":         year,
        })
    return rows


def get_all_fmr(year=FMR_YEAR, force_refresh=False):
    cache_name = f"fmr_all_{year}"
    if not force_refresh:
        cached = _load_cache(cache_name)
        if cached is not None:
            return cached

    states   = get_states()
    all_rows = []
    for _, row in states.iterrows():
        rows = _fetch_fmr_state(row["state_code"], year)
        all_rows.extend(rows)
        time.sleep(0.5)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["fips5"] = df["fips_code"].astype(str).str[:5]
    df["display_name"] = df.apply(
        lambda r: r["town_name"] if r["town_name"] else r["county_name"], axis=1
    )
    max_2br = df["br2_fmr"].max()
    df["rent_index"] = ((df["br2_fmr"] / max_2br) * 100).round(2) if max_2br > 0 else 0.0
    _save_cache(df, cache_name)
    return df


# ── Income Limits (per-county via /il/data/{fips}) ───────────────────────────

def get_all_income_limits(year=FMR_YEAR, force_refresh=False):
    cache_name = f"il_all_{year}"
    if not force_refresh:
        cached = _load_cache(cache_name)
        if cached is not None:
            return cached

    # Load from the downloaded Excel file — instant, no API calls
    xl_path = os.path.join(os.path.dirname(__file__), "il2025.xlsx")
    if not os.path.exists(xl_path):
        print("[INFO] il2025.xlsx not found, skipping Income Limits.")
        return pd.DataFrame()

    print("[INFO] Loading Income Limits from il2025.xlsx...")
    raw = pd.read_excel(xl_path, dtype={"fips": str})

    # Normalize FIPS to 10 digits to match FMR fips_code format
    # Normalize FIPS to match FMR fips_code format
    raw["fips_str"]  = raw["fips"].astype(str).str.strip()
    # FMR uses 10-digit FIPS, Excel uses 9-digit — pad to 10
    raw["fips_code"] = raw["fips"].astype(str).str.strip().str.zfill(10)
    raw["fips5"]     = raw["fips"].astype(str).str.strip().str.zfill(10).str[:5]

    df = raw[["fips_code", "fips5", "median2025", "l50_4", "l80_4"]].copy()
    df = df.rename(columns={
        "median2025": "median_income",
        "l50_4":      "il50_p4",
        "l80_4":      "il80_p4",
    })

    _save_cache(df, cache_name)
    print(f"[INFO] Loaded {len(df):,} areas from Excel.")
    return df

# ── Master dataset ────────────────────────────────────────────────────────────

def get_master_df(year=FMR_YEAR, force_refresh=False):
    fmr = get_all_fmr(year, force_refresh=force_refresh)

    if fmr is None or fmr.empty:
        return pd.DataFrame()

    print("[INFO] Fetching Income Limits per county...")
    il = get_all_income_limits(year, force_refresh=force_refresh)

    if il is None or il.empty:
        df = fmr.copy()
        df["median_income"] = 0.0
        df["il50_p4"]       = 0.0
        df["il80_p4"]       = 0.0
    else:
        df = fmr.merge(
            il[["fips5", "median_income", "il50_p4", "il80_p4"]],
            on="fips5", how="left",
        )
        df["median_income"] = df["median_income"].fillna(0.0)
        df["il50_p4"]       = df["il50_p4"].fillna(0.0)
        df["il80_p4"]       = df["il80_p4"].fillna(0.0)

    df["annual_2br_rent"] = df["br2_fmr"] * 12
    df["rent_burden_pct"] = np.where(
        df["median_income"] > 0,
        (df["annual_2br_rent"] / df["median_income"] * 100).round(1),
        np.nan,
    )

    def _burden_label(pct):
        if pd.isna(pct):  return "Unknown"
        if pct < 30:      return "Affordable (<30%)"
        if pct < 50:      return "Cost-Burdened (30–50%)"
        return "Severely Burdened (>50%)"

    df["burden_category"] = df["rent_burden_pct"].apply(_burden_label)

    max_burden = df["rent_burden_pct"].max()
    df["livability_score"] = np.where(
        df["rent_burden_pct"].notna() & (max_burden > 0),
        (100 - (df["rent_burden_pct"] / max_burden * 100)).round(2),
        np.nan,
    )

    return df


# ── Trend data ────────────────────────────────────────────────────────────────

def get_trend_data(state_code, force_refresh=False):
    cache_name = f"trend_{state_code}"
    if not force_refresh:
        cached = _load_cache(cache_name)
        if cached is not None:
            return cached

    all_rows = []
    for year in TREND_YEARS:
        rows = _fetch_fmr_state(state_code, year)
        all_rows.extend(rows)
        time.sleep(0.5)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["display_name"] = df.apply(
        lambda r: r["town_name"] if r["town_name"] else r["county_name"], axis=1
    )
    _save_cache(df, cache_name)
    return df


def get_all_states_trend(force_refresh=False):
    cache_name = "trend_all"
    if not force_refresh:
        cached = _load_cache(cache_name)
        if cached is not None:
            return cached

    states   = get_states()
    all_rows = []
    for _, row in states.iterrows():
        sc = row["state_code"]
        for year in TREND_YEARS:
            rows = _fetch_fmr_state(sc, year)
            all_rows.extend(rows)
            time.sleep(0.5)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["display_name"] = df.apply(
        lambda r: r["town_name"] if r["town_name"] else r["county_name"], axis=1
    )
    _save_cache(df, cache_name)
    return df