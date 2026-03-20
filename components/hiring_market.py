"""
components/hiring_market.py
Phase 2c — Hiring Market Explorer
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd


def render(df: pd.DataFrame, br_col: str, bedroom_label: str, selected_state: str):
    st.header("🎯 Hiring Market Explorer")
    st.caption(
        "Find the best counties to hire remote talent — balancing low cost-of-living "
        "with high livability. Low rent index = budget-friendly. High livability = good for employees."
    )

    if df.empty:
        st.warning("No data for selected filters.")
        return

    # ── Filter controls ───────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        max_index = st.slider("Max Rent Index (cost ceiling)", 10, 100, 60, key="hire_max_idx")
    with ctrl2:
        min_livability = st.slider("Min Livability Score", 0, 100, 30, key="hire_min_liv")
    with ctrl3:
        top_n = st.slider("Show Top N Markets", 5, 50, 20, key="hire_n")

    filtered = df[
        (df["rent_index"] <= max_index) &
        (df["livability_score"].fillna(0) >= min_livability)
    ].copy().sort_values("livability_score", ascending=False).head(top_n)

    k1, k2, k3 = st.columns(3)
    k1.metric("Markets Found",        len(filtered))
    k2.metric("Avg Rent Index",       f"{filtered['rent_index'].mean():.1f}" if not filtered.empty else "—")
    k3.metric("Avg Livability Score", f"{filtered['livability_score'].mean():.1f}" if not filtered.empty else "—")

    if filtered.empty:
        st.warning("No markets match the current filters. Try relaxing the constraints.")
        return

    st.divider()

    # ── Scatter: Rent Index vs Livability ─────────────────────────────────────
    fig_scatter = px.scatter(
        filtered,
        x="rent_index",
        y="livability_score",
        size=br_col,
        color="state_code",
        hover_name="display_name",
        hover_data={
            "state_code":       True,
            br_col:             ":$,.0f",
            "rent_index":       ":.1f",
            "livability_score": ":.1f",
            "rent_burden_pct":  ":.1f",
            "median_income":    ":$,.0f",
            "fips5":            False,
        },
        labels={
            "rent_index":       "Rent Index (lower = cheaper to hire)",
            "livability_score": "Livability Score (higher = better for employee)",
            br_col:             f"{bedroom_label} FMR ($)",
            "state_code":       "State",
        },
        title="Hiring Sweet Spot: Low Cost + High Livability",
        size_max=22,
    )
    fig_scatter.add_shape(
        type="rect", x0=0, x1=40, y0=60, y1=100,
        fillcolor="rgba(34,197,94,0.08)",
        line_color="rgba(34,197,94,0.35)",
        line_width=1.5,
    )
    fig_scatter.add_annotation(
        x=20, y=96, text="✅ Ideal Hiring Zone",
        showarrow=False, font=dict(color="#4ADE80", size=12),
    )
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        font_color="#E6EDF3",
        height=500,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    # ── Top markets table ─────────────────────────────────────────────────────
    st.subheader("🏆 Top Budget-Friendly Markets")
    table = filtered[[
        "display_name", "state_code", "rent_index", br_col,
        "livability_score", "rent_burden_pct", "median_income", "burden_category",
    ]].reset_index(drop=True)
    table.index += 1
    table.columns = [
        "County", "State", "Rent Index", f"{bedroom_label} FMR ($)",
        "Livability Score", "Rent Burden (%)", "Median Income ($)", "Burden Category",
    ]
    st.dataframe(
        table.style.format({
            f"{bedroom_label} FMR ($)": "${:,.0f}",
            "Rent Index":               "{:.1f}",
            "Livability Score":         "{:.1f}",
            "Rent Burden (%)":          "{:.1f}%",
            "Median Income ($)":        "${:,.0f}",
        }).background_gradient(subset=["Livability Score"], cmap="Greens"),
        use_container_width=True,
        height=420,
    )

    st.divider()

    # ── States with most affordable counties ──────────────────────────────────
    st.subheader("📊 Budget Markets by State")
    state_counts = (
        df[df["rent_index"] <= max_index]
        .groupby("state_code")
        .size()
        .reset_index(name="affordable_counties")
        .sort_values("affordable_counties", ascending=False)
        .head(20)
    )
    fig_bar = px.bar(
        state_counts,
        x="state_code", y="affordable_counties",
        color="affordable_counties",
        color_continuous_scale="Blues",
        title=f"States with Most Counties Having Rent Index ≤ {max_index}",
        labels={"state_code": "State", "affordable_counties": "# of Counties"},
        text="affordable_counties",
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E6EDF3",
        height=380,
        showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)