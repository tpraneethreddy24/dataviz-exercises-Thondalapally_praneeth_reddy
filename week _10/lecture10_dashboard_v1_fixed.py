#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 18:50:24 2026

@author: dina.deifallah
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path



# @st.cache_data: Streamlit reruns the entire script on every widget interaction.
# Without caching, the CSV is read from disk on every interaction — slow and wasteful.
# cache_data stores the result after the first run and reuses it until the file changes

@st.cache_data
def load_data():
    path = Path(__file__).parent.parent / 'data' / 'co2_emissions.csv'
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-01-01')
    return df

df = load_data()

st.title("CO₂ Emissions Explorer")

with st.sidebar:
    st.header("Filters")
    
    # filter 1: Multi-select country
    selected_countries = st.multiselect(
        "Countries", sorted(df['Country'].unique()),
        default=['China', 'United States', 'India', 'Germany']
    )
    
    # guard against empty country selection
    if not selected_countries:
        st.warning("Select at least one country.")
        st.stop()
          
    
    # filter 2: slider for year range - use when year is cast as an integer
    # Tuple default → two-handle range slider
    year_range = st.slider("Year range",
        int(df['Year'].min()), int(df['Year'].max()), (2010, 2020))
    
    
# applying filtering by country and year range 
filtered = df[
    df['Country'].isin(selected_countries) &
    (df['Year'] >= year_range[0]) &
    (df['Year'] <= year_range[1])
]

# for clarity: showing the number of countries and the number of data points selected
st.caption(f"Showing {len(selected_countries)} countries | {len(filtered)} data points")


# Figure 1: Line chart
### Class exercise (SOLVED): fixed the 'too many colours' issue by using a
### highlight colour for one country only and grey for the rest.
### BBD colour type: HIGHLIGHT — the eye should go to one series, not 26.

import plotly.graph_objects as go

# Pick the country with the highest total CO2 over the filtered range as the
# one that gets to "stand out" — everyone else fades into the background.
highlight_country = (
    filtered.groupby('Country')['CO2_Mt'].sum().idxmax()
)

fig = go.Figure()
for country in selected_countries:
    country_df = filtered[filtered['Country'] == country].sort_values('Year')
    is_highlighted = country == highlight_country
    fig.add_trace(go.Scatter(
        x=country_df['Year'], y=country_df['CO2_Mt'],
        mode='lines',
        name=country,
        line=dict(color='#E63946' if is_highlighted else '#D9D9D9',
                  width=3 if is_highlighted else 1.5),
        showlegend=not is_highlighted  # highlighted line is labelled directly
    ))
    if is_highlighted and not country_df.empty:
        last_row = country_df.iloc[-1]
        fig.add_annotation(
            x=last_row['Year'], y=last_row['CO2_Mt'],
            text=f" {country}", showarrow=False,
            xanchor='left', font=dict(color='#E63946', size=12)
        )

fig.update_layout(
    title=f'CO2 (Mt) over time — {highlight_country} highlighted',
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='Arial'), yaxis_title='CO2 (Mt)', xaxis_title=''
)
st.plotly_chart(fig, use_container_width=True)













