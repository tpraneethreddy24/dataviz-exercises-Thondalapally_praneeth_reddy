import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import datetime

st.set_page_config(page_title="CO2 Dashboard", page_icon="🌱", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
# @st.cache_data: Streamlit reruns the entire script on every widget interaction.
# Without caching, the CSV is read from disk on every interaction — slow and wasteful.
# cache_data stores the result after the first run and reuses it until the file changes.
@st.cache_data
def load_data():
    path = Path(__file__).parent.parent / 'data' / 'co2_emissions.csv'
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-01-01')
    return df

df = load_data()

st.title("🌱 CO2 Emissions Explorer")
st.caption("Source: Our World in Data — ourworldindata.org/co2-emissions")

# ── TASK 1: Sidebar with 5 widgets ────────────────────────────────────────────
#   a) st.selectbox for Region (with 'All')
#   b) st.multiselect for Countries (updates based on region — chained)
#   c) st.date_input for date range (two-handle; convert years to Jan-1 dates)
#   d) st.radio for Metric: "Total CO2 (Mt)" vs "CO2 per capita"
#   e) st.checkbox labelled "Show only top emitter highlighted"
#
# Guards:
#   - empty countries → st.warning + st.stop()
#   - incomplete date_input → st.warning + st.stop()
# Convert date_input result to pd.Timestamp before filtering.
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    # a) Region — chained filter driver
    regions = ['All'] + sorted(df['Region'].unique())
    selected_region = st.selectbox("Region", regions)

    # b) Countries — narrowed by region (chained filter)
    if selected_region == 'All':
        country_options = sorted(df['Country'].unique())
    else:
        country_options = sorted(df[df['Region'] == selected_region]['Country'].unique())
    selected_countries = st.multiselect(
        "Countries", country_options, default=country_options[:3]
    )

    # guard against empty country selection
    if not selected_countries:
        st.warning("Select at least one country.")
        st.stop()

    # c) Date range — real calendar picker (data has Jan-1 timestamps)
    date_range = st.date_input(
        "Date range",
        value=(datetime.date(2005, 1, 1), datetime.date(2020, 1, 1)),
        min_value=datetime.date(int(df['Year'].min()), 1, 1),
        max_value=datetime.date(int(df['Year'].max()), 1, 1),
        format="YYYY-MM-DD"
    )

    # guard against user having clicked start but not end yet
    if len(date_range) != 2:
        st.warning("Select a start AND end date.")
        st.stop()

    st.divider()

    # d) Metric — 2 exclusive options, radio is clearer than a selectbox here
    metric = st.radio("Metric", ["Total CO2 (Mt)", "CO2 per capita"])

    # e) Highlight toggle — drives the SWD grey-and-highlight treatment below
    highlight_top = st.checkbox("Show only top emitter highlighted")

# Always convert date_input's date objects → pd.Timestamp before pandas comparisons
start_ts, end_ts = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])

y_col = 'CO2_Mt' if metric == "Total CO2 (Mt)" else 'CO2_per_capita'
y_label = 'CO2 Emissions (Mt)' if y_col == 'CO2_Mt' else 'CO2 per Capita'

filtered = df[
    df['Country'].isin(selected_countries) &
    (df['Date'] >= start_ts) &
    (df['Date'] <= end_ts)
]

# guard against empty filtered data
if filtered.empty:
    st.warning("No data in this date range for the selected countries.")
    st.stop()

# ── TASK 2: Filter summary caption ────────────────────────────────────────────
# Show: "X countries | Region | Date range | Metric"
# BBD rule: always show users how many records match current filters
# ─────────────────────────────────────────────────────────────────────────────
st.caption(
    f"{len(selected_countries)} countries | {selected_region} | "
    f"{date_range[0].strftime('%d %b %Y')} – {date_range[1].strftime('%d %b %Y')} | {metric}"
)

# ── TASK 3: Two charts reacting to ALL filters ────────────────────────────────
#   Left: line chart — selected metric over time, one line per country
#         If "Show only top emitter highlighted" checkbox is on:
#           - grey all lines except the highest emitter in the date range
#           - label that country at the end of its line (SWD grey-and-highlight)
#   Right: bar chart — ranking for the last year in selected date range
#
# BBD colour requirement: name the colour type in a comment next to each chart
# SWD requirements: white background, insight title, use_container_width=True
# ─────────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    if highlight_top:
        # SWD grey-and-highlight: one country in colour, the rest in neutral grey.
        # BBD colour type: HIGHLIGHT — a single series needs to stand out from the group.
        totals = filtered.groupby('Country')[y_col].sum()
        top_country = totals.idxmax()

        fig1 = go.Figure()
        for country in selected_countries:
            country_df = filtered[filtered['Country'] == country].sort_values('Year')
            is_top = country == top_country
            fig1.add_trace(go.Scatter(
                x=country_df['Year'], y=country_df[y_col],
                mode='lines',
                name=country,
                line=dict(color='#E63946' if is_top else '#D9D9D9',
                          width=3 if is_top else 1.5),
                showlegend=not is_top  # top emitter is labelled directly instead
            ))
            if is_top and not country_df.empty:
                last_row = country_df.iloc[-1]
                fig1.add_annotation(
                    x=last_row['Year'], y=last_row[y_col],
                    text=f" {country}", showarrow=False,
                    xanchor='left', font=dict(color='#E63946', size=12)
                )

        fig1.update_layout(
            title=f'{metric} over time — {top_country} highlighted as top emitter',
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Arial'),
            yaxis_title=y_label, xaxis_title=''
        )
    else:
        # BBD colour type: CATEGORICAL — each country is an unordered group
        fig1 = px.line(filtered, x='Year', y=y_col, color='Country',
                        labels={y_col: y_label},
                        title=f'{metric} over time')
        fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                            font=dict(family='Arial'))

    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    # BBD colour type: HIGHLIGHT — single bold colour draws the eye to the ranking
    latest = filtered[filtered['Year'] == filtered['Year'].max()].sort_values(y_col)
    fig2 = px.bar(latest, x=y_col, y='Country', orientation='h',
                  color_discrete_sequence=['#2E75B6'],
                  title=f'Latest year ranking — {metric}')
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                        font=dict(family='Arial'),
                        xaxis=dict(range=[0, latest[y_col].max() * 1.15]))
    fig2.update_traces(marker_line_width=0)
    st.plotly_chart(fig2, use_container_width=True)

# ── EXTENSION: KPI row above the charts ───────────────────────────────────────
#   - Total CO2 in last year of selected range (sum across selected countries)
#   - % change from first to last year
#   - Country with highest emissions in last year
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Key numbers for this selection")

first_year, last_year = filtered['Year'].min(), filtered['Year'].max()
total_last_year = filtered[filtered['Year'] == last_year][y_col].sum()
total_first_year = filtered[filtered['Year'] == first_year][y_col].sum()
pct_change = ((total_last_year - total_first_year) / total_first_year * 100
              if total_first_year else 0)
top_last_year = (filtered[filtered['Year'] == last_year]
                  .sort_values(y_col, ascending=False)
                  .iloc[0]['Country'])

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(f"Total {metric} ({last_year})", f"{total_last_year:,.1f}")
kpi2.metric(f"Change {first_year}→{last_year}", f"{pct_change:+.1f}%")
kpi3.metric(f"Top emitter ({last_year})", top_last_year)
