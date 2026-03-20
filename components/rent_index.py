"""
components/rent_index.py
Phase 1 MVP — Choropleth map + rent burden overlay + ranked table
"""

import plotly.express as px
import streamlit as st
import pandas as pd


def render(df: pd.DataFrame, br_col: str, bedroom_label: str, selected_state: str):
    st.header("🗺️ U.S. Rent Index Map")
    st.caption(
        "Each county is scored 0–100 relative to the most expensive market. "
        "Score 100 = highest rent. Use this index to adjust remote employee salaries."
    )

    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    # ── KPI metrics ───────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    top_row  = df.loc[df[br_col].idxmax()]
    low_row  = df.loc[df[br_col].idxmin()]
    avg_fmr  = df[br_col].mean()
    burdened = df[df["burden_category"].str.contains("Burdened", na=False)]

    col1.metric(
        "📍 Most Expensive",
        top_row["display_name"],
        f"${top_row[br_col]:,.0f}/mo · Index 100",
    )
    col2.metric(
        "📍 Most Affordable",
        low_row["display_name"],
        f"${low_row[br_col]:,.0f}/mo · Index {low_row['rent_index']:.1f}",
    )
    col3.metric("📊 Avg FMR", f"${avg_fmr:,.0f}/mo", bedroom_label)
    col4.metric(
        "⚠️ Cost-Burdened Counties",
        f"{len(burdened):,}",
        f"of {len(df):,} total",
        delta_color="inverse",
    )

    st.divider()

    # ── Map toggle ────────────────────────────────────────────────────────────
    map_mode = st.radio(
        "Map View",
        ["Rent Index", "Rent Burden %"],
        horizontal=True,
        help="Rent Index = cost relative to most expensive county. Rent Burden = % of median income spent on rent.",
    )

    if map_mode == "Rent Index":
        color_col   = "rent_index"
        color_scale = "RdYlGn_r"
        color_range = [0, 100]
        color_label = "Rent Index (0–100)"
        title       = f"Rent Index by County — {bedroom_label} (FY2025)"
    else:
        color_col   = "rent_burden_pct"
        color_scale = "RdYlGn_r"
        color_range = [10, 80]
        color_label = "Rent Burden (%)"
        title       = "Rent Burden by County — Annual 2BR Rent as % of Median Income"

    plot_df = df.dropna(subset=[color_col]) if map_mode == "Rent Burden %" else df

    fig = px.choropleth(
        plot_df,
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
        locations="fips5",
        color=color_col,
        color_continuous_scale=color_scale,
        range_color=color_range,
        scope="usa",
        hover_name="display_name",
        hover_data={
            "state_code":      True,
            br_col:            ":$,.0f",
            "rent_index":      ":.1f",
            "rent_burden_pct": ":.1f",
            "burden_category": True,
            "median_income":   ":$,.0f",
            "fips5":           False,
        },
        labels={
            br_col:            f"{bedroom_label} FMR ($)",
            "rent_index":      "Rent Index",
            "rent_burden_pct": "Rent Burden (%)",
            "burden_category": "Burden Category",
            "median_income":   "Median Income ($)",
            "state_code":      "State",
        },
        title=title,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E6EDF3",
        coloraxis_colorbar=dict(title=color_label),
        margin=dict(l=0, r=0, t=40, b=0),
        height=540,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Burden breakdown pie ──────────────────────────────────────────────────
    burden_counts = df["burden_category"].value_counts().reset_index()
    burden_counts.columns = ["Category", "Count"]
    pie_colors = {
        "Affordable (<30%)":        "#16A34A",
        "Cost-Burdened (30–50%)":   "#D97706",
        "Severely Burdened (>50%)": "#DC2626",
        "Unknown":                  "#475569",
    }
    fig_pie = px.pie(
        burden_counts,
        names="Category",
        values="Count",
        color="Category",
        color_discrete_map=pie_colors,
        title="Rent Burden Distribution Across Counties",
        hole=0.4,
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#E6EDF3",
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # ── Ranked table ──────────────────────────────────────────────────────────
    st.subheader("📋 County Rankings")
    c1, c2 = st.columns([1, 3])
    with c1:
        show_n = st.slider("Show top N counties", 10, 200, 25)
    with c2:
        sort_by = st.radio(
            "Sort by",
            ["Rent Index ↓", "Rent Burden % ↓", "Livability Score ↓"],
            horizontal=True,
        )

    sort_col = {
        "Rent Index ↓":       "rent_index",
        "Rent Burden % ↓":    "rent_burden_pct",
        "Livability Score ↓": "livability_score",
    }[sort_by]

    table = (
        df[[
            "display_name", "state_code", "rent_index", br_col,
            "rent_burden_pct", "burden_category", "median_income", "livability_score",
        ]]
        .sort_values(sort_col, ascending=False)
        .head(show_n)
        .reset_index(drop=True)
    )
    table.index += 1
    table.columns = [
        "County", "State", "Rent Index", f"{bedroom_label} FMR ($)",
        "Rent Burden (%)", "Burden Category", "Median Income ($)", "Livability Score",
    ]

    st.dataframe(
        table.style.format({
            f"{bedroom_label} FMR ($)": "${:,.0f}",
            "Rent Index":               "{:.1f}",
            "Rent Burden (%)":          "{:.1f}%",
            "Median Income ($)":        "${:,.0f}",
            "Livability Score":         "{:.1f}",
        }).background_gradient(subset=["Rent Index"], cmap="RdYlGn_r"),
        use_container_width=True,
        height=420,
    )