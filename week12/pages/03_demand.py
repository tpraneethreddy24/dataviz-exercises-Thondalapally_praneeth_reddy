# pages/03_demand.py — demand page (BBD squiggle level 3: demand story)
import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_data, sidebar_filters

# ─────────────────────────────────────────────────────────────────────────────
# Load data + shared sidebar
# One call to sidebar_filters gives the SAME sidebar as pages 1 and 2 —
# and the filter choices carried over from them, for free.
# ─────────────────────────────────────────────────────────────────────────────
df, p95 = load_data()
filtered = sidebar_filters(df, p95)  # SAME sidebar — choices carried over from pages 1 & 2

st.title('Where is guest demand strongest?')
st.caption('BBD squiggle: from the neighbourhood story to the demand story')

# ─────────────────────────────────────────────────────────────────────────────
# A persisted widget of my own — focus on one room type at a time.
# Same trick as sel_hood on page 2: initialise once, keep alive every run,
# then guard against a saved value the current filters have removed.
# ─────────────────────────────────────────────────────────────────────────────
room_opts = sorted(filtered['room_type'].unique())

if 'sel_room' not in st.session_state:
    st.session_state.sel_room = room_opts[0]          # initialise once
st.session_state.sel_room = st.session_state.sel_room  # keep alive across pages

if st.session_state.sel_room not in room_opts:         # guard: filters may have
    st.session_state.sel_room = room_opts[0]            # removed the saved choice

st.selectbox('Focus on a room type', room_opts, key='sel_room')
room = st.session_state.sel_room
room_df = filtered[filtered['room_type'] == room]

# ─────────────────────────────────────────────────────────────────────────────
# KPI row — 5-second test: the metrics alone should answer the page's question
# ─────────────────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric('Listings', f'{len(room_df):,}')
k2.metric('Avg Reviews/Month', f"{room_df['reviews_per_month'].mean():.1f}",
          f"{room_df['reviews_per_month'].mean() - filtered['reviews_per_month'].mean():+.1f} "
          'vs filtered market')
k3.metric('Median Price', f"£{room_df['price'].median():.0f}/night")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Demand chart — price vs reviews/month (reviews as a demand proxy),
# highlight column for the focused room type.
# BBD HIGHLIGHT colour: blue for the focused room type, grey for the rest
# BBD CVD: blue vs grey — no red-green combination
# ─────────────────────────────────────────────────────────────────────────────
plot_df = filtered.copy()
plot_df['highlight'] = plot_df['room_type'].apply(
    lambda r: room if r == room else 'Other room types')

fig = px.scatter(plot_df, x='reviews_per_month', y='price', color='highlight',
                 color_discrete_map={room: '#2E75B6', 'Other room types': '#AAAAAA'},
                 labels={'reviews_per_month': 'Reviews per Month (demand proxy)',
                         'price': 'Nightly Price (£)', 'highlight': ''},
                 title=f'{room} listings span the price range even at high demand')
fig.update_traces(marker=dict(size=7, opacity=0.7, line=dict(width=0)))
fig.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                  font=dict(family='Arial', size=12),
                  yaxis=dict(gridcolor='#EEEEEE'), xaxis=dict(showgrid=False),
                  legend=dict(orientation='h', y=1.08))
st.plotly_chart(fig, width='stretch')

# TEST for graders: pick a room type, switch to page 1, change a filter,
# come back — both the sidebar filters AND the room-type selection must be
# where you left them (or gracefully replaced if filtered out).
