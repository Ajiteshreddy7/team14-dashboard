"""
components/trends.py
Phase 2d — Rent Trend Tracker (multi-year FMR 2021–2025)
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.fmr_data import get_trend_data, TREND_YEARS


def render(df: pd.DataFrame, df_trends, br_col: str, bedroom_label: str):
    st.header("📈 Rent Trend Tracker")
    st.caption(
        "Track how Fair Market Rents have changed year-over-year (2021–2025). "
        "Identify fast-rising markets — a key risk signal for HR teams setting salary bands."
    )

    # ── State-level overview (always available) ───────────────────────────────
    st.subheader("State-Level Average FMR Overview")
    state_avg = (
        df.groupby("state_code")[["br0_fmr","br1_fmr","br2_fmr","br3_fmr","br4_fmr"]]
        .mean()
        .reset_index()
        .sort_values(br_col, ascending=False)
    )
    fig_state = px.bar(
        state_avg.head(30),
        x="state_code", y=br_col,
        color=br_col,
        color_continuous_scale="RdYlGn_r",
        title=f"Average {bedroom_label} FMR by State (FY2025)",
        labels={"state_code": "State", br_col: f"{bedroom_label} FMR ($)"},
        text=state_avg.head(30)[br_col].apply(lambda v: f"${v:,.0f}"),
    )
    fig_state.update_traces(textposition="outside")
    fig_state.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E6EDF3",
        height=400,
        showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_state, use_container_width=True)

    st.divider()

    # ── Multi-year trend (requires button click to load) ──────────────────────
    if df_trends is None or (hasattr(df_trends, "empty") and df_trends.empty):
        st.info(
            "👆 Click **Load Trend Data (2021–2025)** above to fetch multi-year rent history. "
            "This makes ~250 API calls and takes about 3 minutes. "
            "Results are cached — only needed once."
        )
        return

    st.subheader("📅 County-Level Trend Analysis (2021–2025)")

    col1, col2, col3 = st.columns(3)
    state_list = sorted(df_trends["state_code"].unique().tolist())
    with col1:
        trend_state = st.selectbox("Select State", state_list, key="trend_state")
    with col2:
        br_map = {
            "Studio (0BR)": "br0_fmr",
            "1 Bedroom":    "br1_fmr",
            "2 Bedroom":    "br2_fmr",
            "3 Bedroom":    "br3_fmr",
            "4 Bedroom":    "br4_fmr",
        }
        trend_br_label = st.selectbox("Bedroom Size", list(br_map.keys()), index=2, key="trend_br")
        trend_br_col   = br_map[trend_br_label]
    with col3:
        top_n = st.slider("Counties to show", 3, 15, 8, key="trend_n")

    state_trend = df_trends[df_trends["state_code"] == trend_state].copy()
    if state_trend.empty:
        st.warning(f"No trend data for {trend_state}.")
        return

    state_trend["year"] = state_trend["year"].astype(int)
    state_trend["display_name"] = state_trend.apply(
        lambda r: r["town_name"] if r["town_name"] else r["county_name"], axis=1
    )

    latest_year = state_trend["year"].max()
    first_year  = state_trend["year"].min()

    top_counties = (
        state_trend[state_trend["year"] == latest_year]
        .nlargest(top_n, trend_br_col)["display_name"]
        .tolist()
    )
    plot_df = state_trend[state_trend["display_name"].isin(top_counties)]

    # Growth stats
    growth_df = (
        state_trend[state_trend["year"].isin([first_year, latest_year])]
        .groupby(["display_name", "year"])[trend_br_col]
        .mean()
        .unstack(level=1)
        .dropna()
    )
    avg_growth = 0
    if first_year in growth_df.columns and latest_year in growth_df.columns:
        growth_df["pct_growth"] = (
            (growth_df[latest_year] - growth_df[first_year]) / growth_df[first_year] * 100
        ).round(1)
        fastest    = growth_df["pct_growth"].idxmax()
        slowest    = growth_df["pct_growth"].idxmin()
        avg_growth = growth_df["pct_growth"].mean()

        g1, g2, g3 = st.columns(3)
        g1.metric("📈 Fastest Rising", fastest,
                  f"+{growth_df.loc[fastest,'pct_growth']:.1f}% since {first_year}")
        g2.metric("📉 Slowest Growth", slowest,
                  f"{growth_df.loc[slowest,'pct_growth']:+.1f}% since {first_year}")
        g3.metric("📊 State Avg Growth", f"{avg_growth:.1f}%", f"{first_year}→{latest_year}")

    # ── Line chart ────────────────────────────────────────────────────────────
    fig_line = px.line(
        plot_df,
        x="year", y=trend_br_col,
        color="display_name",
        markers=True,
        hover_name="display_name",
        hover_data={"year": True, trend_br_col: ":$,.0f"},
        labels={
            "year":         "Year",
            trend_br_col:   f"{trend_br_label} FMR ($)",
            "display_name": "County",
        },
        title=f"FMR Trend — {trend_state} | {trend_br_label} (Top {top_n} Counties)",
    )
    fig_line.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        font_color="#E6EDF3",
        height=450,
        xaxis=dict(tickmode="linear", dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # ── Growth leaderboard ────────────────────────────────────────────────────
    if not growth_df.empty and "pct_growth" in growth_df.columns:
        st.subheader(f"📊 Rent Growth Leaderboard — {trend_state} ({first_year}→{latest_year})")
        growth_sorted = growth_df.reset_index().sort_values("pct_growth", ascending=False).head(25)

        fig_growth = px.bar(
            growth_sorted,
            x="display_name", y="pct_growth",
            color="pct_growth",
            color_continuous_scale="RdYlGn_r",
            title=f"Cumulative {trend_br_label} Rent Growth by County",
            labels={"display_name": "County", "pct_growth": "Growth (%)"},
            text=growth_sorted["pct_growth"].apply(lambda v: f"{v:+.1f}%"),
        )
        fig_growth.add_hline(
            y=avg_growth, line_dash="dot", line_color="#FACC15",
            annotation_text=f"State avg: {avg_growth:.1f}%",
            annotation_font_color="#FACC15",
        )
        fig_growth.update_traces(textposition="outside")
        fig_growth.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E6EDF3",
            height=400,
            xaxis_tickangle=-45,
            showlegend=False,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_growth, use_container_width=True)
        st.caption(
            "⚠️ Counties with high growth rates are rising-risk markets. "
            "Flag these when setting long-term salary bands."
        )