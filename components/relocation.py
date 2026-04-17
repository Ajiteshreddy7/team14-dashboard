"""
components/relocation.py
Phase 2b — Relocation Affordability Tool
Purpose: "If this employee MOVES, what salary do they need to maintain their standard of living?"
"""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd
from components import ai_helpers


def render(df, br_col, bedroom_label):
    st.header("✈️ Relocation Affordability Tool")
    st.caption(
        "Answer: *If an employee moves from City A to City B, what salary do they need "
        "to maintain the same standard of living?* Compare rent burden before and after relocation."
    )

    if df.empty:
        st.warning("No data available.")
        return

    state_list = sorted(df["state_code"].unique().tolist())

    col_orig, col_dest = st.columns(2)

    with col_orig:
        st.subheader("📍 Moving FROM")
        orig_state   = st.selectbox("Origin State", state_list,
                                    index=state_list.index("CA") if "CA" in state_list else 0,
                                    key="rel_orig_state")
        orig_options = sorted(df[df["state_code"] == orig_state]["display_name"].unique().tolist())
        orig_county  = st.selectbox("Origin County", orig_options, key="rel_orig_county")

    with col_dest:
        st.subheader("📍 Moving TO")
        dest_state   = st.selectbox("Destination State", state_list,
                                    index=state_list.index("TX") if "TX" in state_list else 1,
                                    key="rel_dest_state")
        dest_options = sorted(df[df["state_code"] == dest_state]["display_name"].unique().tolist())
        dest_county  = st.selectbox("Destination County", dest_options, key="rel_dest_county")

    current_salary = st.number_input(
        "Employee's Current Salary ($)", min_value=20_000, max_value=500_000,
        value=100_000, step=1_000, key="rel_salary",
    )

    # ── Lookup ────────────────────────────────────────────────────────────────
    orig_rows = df[(df["state_code"] == orig_state) & (df["display_name"] == orig_county)]
    dest_rows = df[(df["state_code"] == dest_state) & (df["display_name"] == dest_county)]

    if orig_rows.empty or dest_rows.empty:
        st.warning("One or both counties not found.")
        return

    orig = orig_rows.iloc[0]
    dest = dest_rows.iloc[0]

    orig_fmr     = orig["br2_fmr"]
    dest_fmr     = dest["br2_fmr"]
    pct_change   = ((dest_fmr - orig_fmr) / orig_fmr * 100) if orig_fmr > 0 else 0
    equiv_salary = current_salary * (dest_fmr / orig_fmr) if orig_fmr > 0 else current_salary
    salary_delta = equiv_salary - current_salary

    housing_pct_before         = (orig_fmr * 12 / current_salary * 100) if current_salary > 0 else 0
    housing_pct_after_same     = (dest_fmr * 12 / current_salary * 100) if current_salary > 0 else 0
    housing_pct_after_adjusted = (dest_fmr * 12 / equiv_salary * 100)   if equiv_salary > 0 else 0

    st.divider()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Origin 2BR FMR",      f"${orig_fmr:,.0f}/mo", orig_county)
    k2.metric("Destination 2BR FMR", f"${dest_fmr:,.0f}/mo", dest_county)
    k3.metric("Rent Change",         f"{pct_change:+.1f}%",
              "More expensive" if pct_change > 0 else "Cheaper")
    k4.metric(
        "Salary Needed at Destination",
        f"${equiv_salary:,.0f}",
        delta=f"${salary_delta:+,.0f} adjustment needed",
        delta_color="inverse" if salary_delta > 0 else "normal",
    )

    if pct_change > 10:
        st.error(
            f"🏙️ **Significant cost increase.** Moving from {orig_county} to {dest_county} "
            f"is **{pct_change:.1f}% more expensive**. "
            f"To maintain the same standard of living, salary must increase from "
            f"**${current_salary:,}** to **${equiv_salary:,.0f}** (+${salary_delta:,.0f}). "
            f"If salary stays flat, housing will consume **{housing_pct_after_same:.1f}%** of income."
        )
    elif pct_change < -10:
        st.success(
            f"✅ **Cost of living decreases.** Moving to {dest_county} is "
            f"**{abs(pct_change):.1f}% cheaper**. "
            f"The employee could accept a salary as low as **${equiv_salary:,.0f}** "
            f"and maintain the same living standard — saving the company **${abs(salary_delta):,.0f}**."
        )
    else:
        st.info(f"Similar cost of living between locations (Δ {pct_change:+.1f}%). Minimal salary adjustment needed.")

    st.divider()

    # ── Housing affordability before vs after ─────────────────────────────────
    st.subheader("🏦 Housing Affordability: Before vs After Move")
    st.caption("HUD standard: housing should be ≤30% of income. Above 30% = cost-burdened.")

    scenarios = {
        "Before Move":                 housing_pct_before,
        "After Move (Same Salary)":    housing_pct_after_same,
        "After Move (Adjusted Salary)":housing_pct_after_adjusted,
    }
    colors = ["#16A34A" if v < 30 else ("#D97706" if v < 50 else "#DC2626")
              for v in scenarios.values()]

    fig_burden = go.Figure()
    fig_burden.add_bar(
        x=list(scenarios.keys()),
        y=list(scenarios.values()),
        marker_color=colors,
        text=[f"{v:.1f}%" for v in scenarios.values()],
        textposition="outside",
    )
    fig_burden.add_hline(y=30, line_dash="dash", line_color="#16A34A",
                         annotation_text="30% — Affordable threshold",
                         annotation_font_color="#16A34A")
    fig_burden.add_hline(y=50, line_dash="dash", line_color="#DC2626",
                         annotation_text="50% — Severely burdened",
                         annotation_font_color="#DC2626")
    fig_burden.update_layout(
        title="% of Salary Spent on Housing — Three Scenarios",
        yaxis_title="Housing Cost as % of Salary",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        font_color="#E6EDF3",
        height=380,
        showlegend=False,
    )
    st.plotly_chart(fig_burden, use_container_width=True)

    st.divider()

    # ── Full FMR comparison by bedroom size ───────────────────────────────────
    st.subheader("🛏️ Full FMR Comparison by Bedroom Size")
    br_labels = ["Studio", "1 Bedroom", "2 Bedroom", "3 Bedroom", "4 Bedroom"]
    orig_vals = [orig["br0_fmr"], orig["br1_fmr"], orig["br2_fmr"], orig["br3_fmr"], orig["br4_fmr"]]
    dest_vals = [dest["br0_fmr"], dest["br1_fmr"], dest["br2_fmr"], dest["br3_fmr"], dest["br4_fmr"]]

    fig_bar = go.Figure()
    fig_bar.add_bar(
        name=f"FROM: {orig_county}, {orig_state}",
        x=br_labels, y=orig_vals,
        marker_color="#2563EB",
        text=[f"${v:,.0f}" for v in orig_vals],
        textposition="outside",
    )
    fig_bar.add_bar(
        name=f"TO: {dest_county}, {dest_state}",
        x=br_labels, y=dest_vals,
        marker_color="#DC2626",
        text=[f"${v:,.0f}" for v in dest_vals],
        textposition="outside",
    )
    fig_bar.update_layout(
        barmode="group",
        title="Monthly FMR by Bedroom Size",
        xaxis_title="Bedroom Size",
        yaxis_title="Monthly Rent ($)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        font_color="#E6EDF3",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── Required salary at different housing % targets ────────────────────────
    st.subheader("💡 What Salary is Needed at Destination?")
    st.caption("How much should the employee earn to keep housing at different affordability targets?")

    targets = {
        "25% of income (comfortable)": dest_fmr * 12 / 0.25,
        "30% of income (HUD standard)": dest_fmr * 12 / 0.30,
        "35% of income (stretched)":    dest_fmr * 12 / 0.35,
        "40% of income (burdened)":     dest_fmr * 12 / 0.40,
    }
    t_colors = ["#16A34A", "#16A34A", "#D97706", "#DC2626"]

    fig_targets = go.Figure()
    fig_targets.add_bar(
        x=list(targets.keys()),
        y=list(targets.values()),
        marker_color=t_colors,
        text=[f"${v:,.0f}" for v in targets.values()],
        textposition="outside",
    )
    fig_targets.add_hline(
        y=current_salary, line_dash="dash", line_color="#FACC15",
        annotation_text=f"Current salary: ${current_salary:,}",
        annotation_font_color="#FACC15",
    )
    fig_targets.update_layout(
        title=f"Required Salary in {dest_county} at Different Housing % Targets",
        yaxis_title="Required Annual Salary ($)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        font_color="#E6EDF3",
        height=380,
        showlegend=False,
        xaxis_tickangle=-10,
    )
    st.plotly_chart(fig_targets, use_container_width=True)

    # ── AI relocation recommendation (grounded in HUD rows) ──
    ai_helpers.relocation_verdict(orig, dest, bedroom_label)
