"""
components/salary_calc.py
Phase 2a — Salary Adjustment Calculator
Purpose: "What should I PAY this employee given where they live RIGHT NOW?"
"""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd
from components import ai_helpers
import numpy as np


def render(df, br_col, bedroom_label):
    st.header("💼 Salary Adjustment Calculator")
    st.caption(
        "Answer: *What should we pay this employee given their local cost of living?* "
        "Uses 2BR Fair Market Rent as the HR standard benchmark for housing costs."
    )

    if df.empty:
        st.warning("No data available.")
        return

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("👤 Employee Details")
        state_list = sorted(df["state_code"].unique().tolist())
        emp_state  = st.selectbox("Employee's State", state_list, key="sal_state")

        county_options = sorted(
            df[df["state_code"] == emp_state]["display_name"].unique().tolist()
        )
        emp_county = st.selectbox("Employee's County", county_options, key="sal_county")

        base_salary = st.number_input(
            "Current/Offered Base Salary ($)",
            min_value=20_000, max_value=500_000,
            value=75_000, step=1_000, key="sal_base",
        )

        st.subheader("🏢 Company Benchmark")
        st.caption("Where is your company HQ or remote baseline set?")
        bench_options = ["National Average"] + state_list
        bench_choice  = st.selectbox("Benchmark Location", bench_options, key="sal_bench")

        if bench_choice != "National Average":
            bench_counties = sorted(
                df[df["state_code"] == bench_choice]["display_name"].unique().tolist()
            )
            bench_county = st.selectbox("Benchmark County", bench_counties, key="sal_bench_county")
        else:
            bench_county = None

    # ── Lookup ────────────────────────────────────────────────────────────────
    emp_rows = df[(df["state_code"] == emp_state) & (df["display_name"] == emp_county)]
    if emp_rows.empty:
        st.warning("County not found.")
        return
    emp_row = emp_rows.iloc[0]
    emp_fmr = emp_row["br2_fmr"]

    if bench_choice == "National Average":
        bench_fmr   = df["br2_fmr"].mean()
        bench_label = "National Average"
    else:
        bench_rows = df[(df["state_code"] == bench_choice) & (df["display_name"] == bench_county)]
        if bench_rows.empty:
            st.warning("Benchmark county not found.")
            return
        bench_fmr   = bench_rows.iloc[0]["br2_fmr"]
        bench_label = f"{bench_county}, {bench_choice}"

    # Core formula: adjust salary proportionally to local rent cost
    adj_factor      = emp_fmr / bench_fmr if bench_fmr > 0 else 1.0
    adjusted_salary = base_salary * adj_factor
    delta           = adjusted_salary - base_salary
    pct_of_salary   = (emp_fmr * 12 / base_salary * 100) if base_salary > 0 else 0

    with col_right:
        st.subheader("📊 Compensation Analysis")
        st.metric(
            "Fair Salary for This Location",
            f"${adjusted_salary:,.0f}",
            delta=f"${delta:+,.0f} vs current salary",
            delta_color="normal" if delta > 0 else "inverse",
        )
        st.metric("Adjustment Factor", f"{adj_factor:.3f}×",
                  help="Employee local 2BR FMR ÷ Benchmark 2BR FMR")
        st.metric("Employee 2BR FMR",  f"${emp_fmr:,.0f}/mo")
        st.metric("Benchmark 2BR FMR", f"${bench_fmr:,.0f}/mo  ({bench_label})")

        rent_burden = emp_row.get("rent_burden_pct")
        if rent_burden and not pd.isna(rent_burden):
            icon = "🟢" if rent_burden < 30 else ("🟡" if rent_burden < 50 else "🔴")
            st.metric(
                f"{icon} Area Rent Burden",
                f"{rent_burden:.1f}%",
                emp_row["burden_category"],
                delta_color="off",
            )

        st.metric(
            "Housing Cost as % of This Salary",
            f"{pct_of_salary:.1f}%",
            "⚠️ Above 30% — consider raising salary" if pct_of_salary > 30 else "✅ Healthy ratio",
            delta_color="off",
        )

        if pct_of_salary > 30:
            st.error(
                f"🚨 At ${base_salary:,}/yr, housing in **{emp_county}** takes "
                f"**{pct_of_salary:.1f}%** of salary. "
                f"Fair salary to keep housing ≤30%: **${emp_fmr * 12 / 0.30:,.0f}**"
            )
        elif delta > base_salary * 0.05:
            st.warning(f"⚠️ Employee is potentially **underpaid** for {emp_county}. Suggested: ${adjusted_salary:,.0f}")
        else:
            st.success(f"✅ Salary is appropriate for {emp_county}.")

    st.divider()

    # ── Gauge ─────────────────────────────────────────────────────────────────
    max_fmr = df["br2_fmr"].max()
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=emp_fmr,
        delta={"reference": bench_fmr, "valueformat": ",.0f", "prefix": "$"},
        title={"text": f"2BR FMR: {emp_county} vs {bench_label}", "font": {"size": 14}},
        gauge={
            "axis":  {"range": [0, max_fmr], "tickprefix": "$"},
            "bar":   {"color": "#2563EB"},
            "steps": [
                {"range": [0,                             df["br2_fmr"].quantile(0.33)], "color": "#14532D"},
                {"range": [df["br2_fmr"].quantile(0.33), df["br2_fmr"].quantile(0.66)], "color": "#78350F"},
                {"range": [df["br2_fmr"].quantile(0.66), max_fmr],                      "color": "#7F1D1D"},
            ],
            "threshold": {
                "line":      {"color": "#FACC15", "width": 4},
                "thickness": 0.75,
                "value":     bench_fmr,
            },
        },
        number={"prefix": "$", "valueformat": ",.0f"},
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#E6EDF3",
        height=300,
        margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.caption("🟡 Yellow line = benchmark FMR. Blue bar = employee's local FMR.")

    st.divider()

    # ── Pay Fairness Scan ─────────────────────────────────────────────────────
    st.subheader(f"📋 Pay Fairness Scan — All Counties in {emp_state}")
    st.caption(
        f"At a flat salary of ${base_salary:,}, which counties are underpaid vs overpaid? "
        f"Red = employee costs more to house than benchmark, they deserve higher pay."
    )

    state_df = df[df["state_code"] == emp_state].copy()
    state_df["fair_salary"] = base_salary * (state_df["br2_fmr"] / bench_fmr)
    state_df["gap"]         = state_df["fair_salary"] - base_salary
    state_df["status"]      = state_df["gap"].apply(
        lambda g: "Underpaid" if g > base_salary * 0.05
        else ("Overpaid" if g < -base_salary * 0.05 else "Fair")
    )
    state_df = state_df.sort_values("fair_salary", ascending=False)

    color_map = {"Underpaid": "#DC2626", "Fair": "#16A34A", "Overpaid": "#2563EB"}
    fig_bar = px.bar(
        state_df,
        x="display_name", y="fair_salary",
        color="status",
        color_discrete_map=color_map,
        title=f"Fair Salary by County in {emp_state} (flat baseline: ${base_salary:,})",
        labels={"display_name": "County", "fair_salary": "Fair Salary ($)", "status": "Pay Status"},
        hover_data={"br2_fmr": ":$,.0f", "gap": ":+$,.0f"},
    )
    fig_bar.add_hline(
        y=base_salary, line_dash="dash", line_color="#FACC15",
        annotation_text=f"Current: ${base_salary:,}",
        annotation_font_color="#FACC15",
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        font_color="#E6EDF3",
        height=420,
        xaxis_tickangle=-45,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption("🔴 Underpaid = employee deserves more | 🟢 Fair | 🔵 Overpaid for location")

    # ── AI fairness check (grounded in HUD row) ──
    ai_helpers.fairness_check(
        location=emp_county,
        bedroom_label=bedroom_label,
        annual_salary=base_salary,
        local_row=emp_row,
    )
