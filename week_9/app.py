#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
World Happiness Dashboard — Final combined app
Steps 1-4 (KPIs + rankings + Score vs GDP) + Step 6 (diverging chart)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# ── Page config ─────────────────────────────────────────────────────────
st.set_page_config(page_title="World Happiness", page_icon="🌍", layout="wide")

# ── Load data ───────────────────────────────────────────────────────────
df = pd.read_csv('data/world_happiness_2023.csv')
df.columns = ['Country', 'Region', 'Score', 'GDP', 'Social_Support',
              'Life_Expectancy', 'Freedom', 'Generosity', 'Corruption']

global_avg = df['Score'].mean()
df['Score_vs_avg'] = df['Score'] - global_avg

# ── Sidebar filters (shared across all charts) ─────────────────────────
with st.sidebar:
    st.header("Filters")
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N", 5, 25, 15)

filtered = df if selected_region == 'All' else df[df['Region'] == selected_region]

# ── Header ──────────────────────────────────────────────────────────────
st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

# ── KPI row — BBD: big numbers at the top, readable in 5 seconds ───────
col1, col2, col3 = st.columns(3)
col1.metric("Countries", len(filtered))
col2.metric("Avg Score", f"{filtered['Score'].mean():.2f}",
            f"{filtered['Score'].mean() - df['Score'].mean():+.2f} vs global")
col3.metric("Happiest", filtered.nlargest(1, 'Score')['Country'].values[0])

st.divider()

# ── Row 1: Rankings + Score vs GDP ──────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Rankings")
    top = filtered.nlargest(top_n, 'Score').sort_values('Score')

    # Highlight colour — single bold colour draws the eye to sorted ranking
    fig1 = px.bar(top, x='Score', y='Country', orientation='h',
                  color_discrete_sequence=['#2E75B6'],
                  labels={'Score': 'Score (0–10)', 'Country': ''})
    fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                        xaxis=dict(range=[0, 8.5]), font=dict(family='Arial', size=12),
                        margin=dict(l=10, r=10, t=5, b=10))
    fig1.update_traces(marker_line_width=0)
    st.plotly_chart(fig1, width='stretch')

with col_right:
    st.subheader("Score vs GDP")
    fig2 = px.scatter(filtered, x='GDP', y='Score', hover_name='Country',
                       color_discrete_sequence=['#E63946'])
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                        font=dict(family='Arial', size=12),
                        margin=dict(l=10, r=10, t=5, b=10))
    st.plotly_chart(fig2, width='stretch')

st.divider()

# ── Row 2: Step 6 — Diverging chart, Score vs Global Average ───────────
st.subheader("Happiness Score vs. Global Average")

top_pos = filtered.nlargest(10, 'Score_vs_avg')
top_neg = filtered.nsmallest(10, 'Score_vs_avg')
plot_df = pd.concat([top_neg, top_pos]).sort_values('Score_vs_avg')

fig3 = px.bar(
    plot_df, x='Score_vs_avg', y='Country', orientation='h',
    color='Score_vs_avg',
    color_continuous_scale='RdBu',   # diverging: red (below) -> white (0) -> blue (above)
    color_continuous_midpoint=0,     # anchors white exactly at the global average
    labels={'Score_vs_avg': f'Deviation from global avg ({global_avg:.2f})', 'Country': ''}
)
fig3.update_layout(
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='Arial', size=12),
    coloraxis_showscale=False,
    margin=dict(l=10, r=20, t=10, b=10)
)
fig3.update_traces(marker_line_width=0)

# Label the midpoint explicitly
fig3.add_vline(x=0, line_width=1.5, line_dash='dash', line_color='#666666')
fig3.add_annotation(
    x=0, y=1.06, yref='paper', showarrow=False,
    text=f'Global average = {global_avg:.2f}',
    font=dict(size=11, color='#666666')
)

st.plotly_chart(fig3, width='stretch')

st.divider()
st.caption("Built with Streamlit + Plotly")
