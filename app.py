"""
app.py  —  Team 14: HUD FMR Cost-of-Living Dashboard
HR Compensation Analysts | Remote Company Salary Tool
"""

import os
import streamlit as st
from components import ai_helpers
from dotenv import load_dotenv
load_dotenv()

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Team 14 | Rent Intelligence Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0D1117; }
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363d;
    }
    [data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #161B22;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: #8b949e;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: white !important;
    }
    h1, h2, h3 { color: #E6EDF3; }
    .stAlert { border-radius: 8px; }
    div[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏠 Rent Intelligence")
    st.markdown("*Team 14 — HR Compensation Analysts*")
    st.divider()

    api_token = st.text_input(
        "HUD API Token",
        type="password",
        value=os.environ.get("HUD_API_TOKEN", ""),
        placeholder="Paste your HUD token here…",
        key="api_token",
    )

    st.divider()

    bedroom_map = {
        "Studio (0BR)": "br0_fmr",
        "1 Bedroom":    "br1_fmr",
        "2 Bedroom":    "br2_fmr",
        "3 Bedroom":    "br3_fmr",
        "4 Bedroom":    "br4_fmr",
    }
    bedroom_label = st.selectbox("Bedroom Size", list(bedroom_map.keys()), index=2)
    br_col = bedroom_map[bedroom_label]

    st.divider()

    load_btn      = st.button("🔄 Load / Refresh Data", use_container_width=True,
                               disabled=not api_token)
    force_refresh = st.checkbox("Force refresh (ignore cache)", value=False)

    st.divider()
    st.markdown("**Data Sources**")
    st.caption("HUD Fair Market Rents FY2025")
    st.caption("HUD Income Limits FY2025")
    st.divider()
    st.markdown(
        "<small style='color:#8b949e'>Team 14 · Visualization Course<br>"
        "HUD FMR Dashboard v1.0</small>",
        unsafe_allow_html=True,
    )

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [("df", None), ("df_trends", None), ("loaded", False)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Set token on module as soon as we have it ─────────────────────────────────
if api_token:
    import data.fmr_data as fmr_module
    fmr_module.API_TOKEN = api_token

# ── Data loading ──────────────────────────────────────────────────────────────
if load_btn and api_token:
    from data.fmr_data import get_master_df
    with st.spinner("Fetching all US counties from HUD API… (~2 min first run, instant after)"):
        df = get_master_df(force_refresh=force_refresh)
    st.session_state["df"]     = df
    st.session_state["loaded"] = True
    st.sidebar.success(f"✅ Loaded {len(df):,} counties")

# Auto-load from cache on rerun if token is present
if not st.session_state["loaded"] and api_token:
    cache_path = os.path.join(os.path.dirname(__file__), "data", ".cache", "fmr_all_2025.csv")
    if os.path.exists(cache_path):
        try:
            from data.fmr_data import get_master_df
            with st.spinner("Loading from cache…"):
                df = get_master_df(force_refresh=False)
            st.session_state["df"]     = df
            st.session_state["loaded"] = True
        except Exception as e:
            st.warning(f"Cache load failed: {e}")

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='margin-bottom:0'>🏠 Rent Intelligence Dashboard</h1>"
    "<p style='color:#8b949e;margin-top:4px'>"
    "HUD Fair Market Rent Analysis · Team 14 · HR Compensation Analysts</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── Landing state (no token) ──────────────────────────────────────────────────
if not api_token:
    st.info("👈 **Enter your HUD API token in the sidebar to get started.**")
    c1, c2, c3, c4, c5 = st.columns(5)
    features = [
        ("🗺️", "Rent Index",      "Score every US county 0–100 relative to most expensive"),
        ("💼", "Salary Calc",     "Adjust employee salaries by local cost of living"),
        ("✈️", "Relocation Tool", "Compare rent burden between any two counties"),
        ("🎯", "Hiring Explorer", "Find budget-friendly talent markets for remote hiring"),
        ("📈", "Trend Tracker",   "5 years of rent growth data with risk flags"),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4, c5], features):
        with col:
            st.markdown(
                f"<div style='background:#161B22;border:1px solid #30363d;"
                f"border-radius:8px;padding:16px;text-align:center;height:160px'>"
                f"<div style='font-size:2rem'>{icon}</div>"
                f"<div style='font-weight:600;margin:8px 0 4px;color:#E6EDF3'>{title}</div>"
                f"<div style='font-size:0.78rem;color:#8b949e'>{desc}</div></div>",
                unsafe_allow_html=True,
            )
    st.stop()

elif not st.session_state["loaded"]:
    st.warning("👈 Click **Load / Refresh Data** in the sidebar to fetch the HUD data.")
    st.stop()

# ── Main app (data loaded) ────────────────────────────────────────────────────
else:
    df = st.session_state["df"]

    with st.sidebar:
        st.divider()
        state_options  = ["All States"] + sorted(df["state_code"].unique().tolist())
        selected_state = st.selectbox("Filter by State", state_options)

    if selected_state == "All States":
        filtered = df.copy()
    else:
        filtered = df[df["state_code"] == selected_state].copy()

    max_br = filtered[br_col].max()
    filtered["rent_index"] = (filtered[br_col] / max_br * 100).round(2) if max_br > 0 else 0.0

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️  Rent Index",
        "💼  Salary Calculator",
        "✈️  Relocation Tool",
        "🎯  Hiring Explorer",
        "📈  Trend Tracker",
    ])

    with tab1:
        from components.rent_index import render
        render(filtered, br_col, bedroom_label, selected_state)
        ai_helpers.insight_card(
            "Rent Index",
            filtered,
            "Summarize the rent-burden landscape for the current bedroom size: "
            "where is it most affordable, where is it most severe, and any outliers?",
            cols=["display_name", "state_code", br_col,
                  "rent_burden_pct", "burden_category", "livability_score"],
            key="ai_rent_index",
        )

    with tab2:
        from components.salary_calc import render
        render(df, br_col, bedroom_label)
        ai_helpers.insight_card(
            "Salary Calculator context",
            df,
            "For the bedroom size selected, which markets offer the healthiest "
            "salary-to-rent ratio (low rent_burden_pct, high median_income)?",
            cols=["display_name", "state_code", br_col,
                  "median_income", "rent_burden_pct", "burden_category"],
            key="ai_salary",
        )

    with tab3:
        from components.relocation import render
        render(df, br_col, bedroom_label)
        ai_helpers.insight_card(
            "Relocation context",
            df,
            "Group the dataset by state_code and call out 2-3 non-obvious "
            "relocation destinations that combine low rent_burden_pct with "
            "above-average livability_score.",
            cols=["display_name", "state_code", br_col,
                  "rent_burden_pct", "burden_category", "livability_score"],
            key="ai_relocation",
        )

    with tab4:
        from components.hiring_market import render
        render(filtered, br_col, bedroom_label, selected_state)
        ai_helpers.insight_card(
            "Hiring Explorer",
            filtered,
            "Which markets in the current filter look like the best hiring destinations "
            "given livability_score, rent_burden_pct, and median_income?",
            cols=["display_name", "state_code", "livability_score",
                  "rent_burden_pct", "median_income", br_col],
            key="ai_hiring",
        )

    with tab5:
        from components.trends import render
        col_btn, col_info = st.columns([2, 5])
        with col_btn:
            if st.button("📥 Load Trend Data (2021–2025)", use_container_width=True):
                import data.fmr_data as fmr_module
                fmr_module.API_TOKEN = api_token
                from data.fmr_data import get_all_states_trend
                with st.spinner("Fetching 5 years of data for all states… (~3 min)"):
                    df_trends = get_all_states_trend(force_refresh=force_refresh)
                    st.session_state["df_trends"] = df_trends
        with col_info:
            if st.session_state["df_trends"] is None:
                st.info("Click the button to load 5 years of rent trend data.")
        render(df, st.session_state.get("df_trends"), br_col, bedroom_label)
        ai_helpers.insight_card(
            "Trend Tracker",
            st.session_state.get("df_trends"),
            "Describe the multi-year FMR trajectory: which states are accelerating, "
            "which are flattening, and name the largest YoY movers.",
            key="ai_trends",
        )

    # ── Natural-language query (global) ──
    with st.expander("🔎 Natural-language query (beta)"):
        ai_helpers.nl_query_box(df)
