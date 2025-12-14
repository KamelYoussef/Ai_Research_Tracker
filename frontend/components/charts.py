import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import streamlit as st
import pydeck as pdk
import pandas as pd
import json
import math
from data.data_processing import transform_value

def plot_pie_chart(data):
    return px.pie(
        data, values="Count", names="Category",
        height=300, hole=0.7,
        color_discrete_sequence=["#1f77b4", "#e377c2"]
    )


def plot_bar_chart(data):
    fig = px.bar(
        data, x="Keyword", y="Visibility score",
        height=350
    )
    fig.update_layout(
        yaxis=dict(range=[0, 100])
    )
    return fig


def plot_group_bar(data):
    fig = px.bar(
        data,
        x='product',  # X-axis: The Insurance Product
        y='Visibility Score (%)',  # Y-axis: The single column containing ALL scores
        color='AI Platform',  # Grouping/Coloring: Separates the bars
        barmode='group',  # Sets the bars side-by-side
        labels={
            "product": "Insurance Product",
            "Visibility Score (%)": "Visibility Score"
        },
        color_discrete_map={
            "CHATGPT": "#1034A6",
            "CLAUDE": "#4682B4",
            "GEMINI": "#6495ED",
            "PERPLEXITY": "#87CEEB"
        }
    )
    fig.update_layout(
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        xaxis_title="Keywords",
        height=350
    )
    return fig


def create_radar_chart(df):
    """
    Creates a radar chart for the given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with a 'product' column and numerical columns.

    Returns:
        plotly.graph_objects.Figure: The radar chart figure.
    """
    fig = go.Figure()

    # Add a trace for each platform
    for platform in df.columns[1:]:  # Exclude 'product' column
        fig.add_trace(go.Scatterpolar(
            r=df[platform].values,  # Percentages for this platform
            theta=df["product"].values,  # Product names as the angular points
            fill='toself',
            name=platform  # Legend entry
        ))

    # Update layout with colors, legend, and sizing
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]  # Adjust range to fit percentage values
            )
        ),
        width=700,
        height=420,
    )
    return fig


def plot_ai_scores_chart(data):
    df = data.reset_index()
    df.columns = ["Month", "Visibility score"]

    month_order = df["Month"].tolist()
    df_segments = df[df["Visibility score"] > 0].copy()

    chart = alt.Chart(df_segments).mark_line(
        point=False,
        #interpolate='monotone',  # Added monotone for a smooth line
        color='#228B22'
    ).encode(
        x=alt.X('Month:N', sort=month_order, axis=alt.Axis(title='')),
        y=alt.Y('Visibility score:Q', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title=''))
    ).properties(
        height=200
    )

    st.altair_chart(chart, width='stretch')


def plot_rank_chart(data):
    df = data.reset_index()
    df.columns = ["month", "rank"]

    # 1. Capture the full month order from the original data
    month_order = df["month"].tolist()

    df_segments = df[df["rank"] > 0].copy()

    # 3. Plot the line using the filtered data.
    chart = alt.Chart(df_segments).mark_line(
        point=False,
        #interpolate='monotone',  # Added monotone for a smooth line
        color='#228B22'
    ).encode(
        # X-axis uses the full month_order for correct chronology
        x=alt.X("month:N", sort=month_order, axis=alt.Axis(title='')),

        # Y-axis scale is inverted for rank (lower is better)
        y=alt.Y("rank:Q", axis=alt.Axis(title=''), scale=alt.Scale(domain=[df["rank"].max(), 1])),
    ).properties(
        height=200
    )

    st.altair_chart(chart, width='stretch')


def display_map_with_score_colors(df_scores):

    # Load location data
    with open("data/geo.json") as f:
        locations = json.load(f)
    df_locations = pd.DataFrame(locations)

    # Merge with scores
    df = df_locations.merge(df_scores, on="location", how="inner")
    df['score'] = df['score'].fillna(0)

    # Map to RGB color: blue (low) → red (high)
    def score_to_color(s):
        # Clamp s between 0 and 100
        s = max(0, min(s, 100))

        # Red decreases from 255 to 0 as s goes 0→100
        r = int((1 - s / 100) * 255)
        # Green increases from 0 to 255 as s goes 0→100
        g = int((s / 100) * 255)
        b = 0

        return [r, g, b, 200]  # Alpha 200 for some transparency

    df['color'] = df['score'].apply(score_to_color)

    # Center view
    center_lat = (df['latitude'].min() + df['latitude'].max()) / 2
    center_lon = (df['longitude'].min() + df['longitude'].max()) / 2

    # Define view state
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=3.6,
        pitch=0
    )

    # Define layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[longitude, latitude]',
        get_color='color',
        get_radius=20000,
        pickable=True
    )

    # Show map
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{location}\nScore: {score}"},
        map_style="mapbox://styles/mapbox/light-v9"
    ))


def plot_sentiment_chart(data):
    df = data.reset_index()
    df.columns = ["month", "sentiment"]

    # Apply your custom transformation function
    df['sentiment'] = df['sentiment'].apply(
        lambda x: transform_value(x) if (x != 'N/A' and x != 0) else x
    )

    # 1. Capture the full 12-month order from the original data
    month_order = df["month"].tolist()

    df_segments = df[~((df["sentiment"] == 'N/A') | (df["sentiment"] == 0))].copy()

    # 3. Plot the line using the filtered data.
    chart = alt.Chart(df_segments).mark_line(
        point=False,
        #interpolate='monotone',  # Added monotone for a smooth line
        color='#228B22'
    ).encode(
        # X-axis uses the full month_order for correct chronology
        x=alt.X('month:N', sort=month_order, axis=alt.Axis(title='')),

        # Y-axis scale is inverted for rank (lower is better)
        y=alt.Y('sentiment:Q', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title=''))
    ).properties(
        height=200
    )

    st.altair_chart(chart, width='stretch')


def display_overview_map(df_scores):
    # Load geo.json with city coordinates
    with open("data/geo.json") as f:
        locations = json.load(f)
    df_locations = pd.DataFrame(locations)  # expects 'location', 'latitude', 'longitude'

    # Merge geo data with scores
    df = df_locations.merge(df_scores, left_on="location", right_on="City", how="left")
    #df['Avg Rank'] = df['Avg Rank'].fillna(0)

    # Cap rank visually at 10
    df['Color Rank'] = df['Avg Rank'].apply(lambda x: min(x, 10))

    # Map rank to RGB color: green (1) → red (10)
    def rank_to_color(rank):
        if rank is None or (isinstance(rank, float) and math.isnan(rank)):
            return [128, 128, 128, 220]  # Black for NaN
        elif rank <= 5:
            return [0, 180, 0, 220]   # Green
        else:
            return [255, 0, 0, 220]  # Red

    df['color'] = df['Color Rank'].apply(rank_to_color)

    # Center view on all points
    center_lat = (df['latitude'].min() + df['latitude'].max()) / 2
    center_lon = (df['longitude'].min() + df['longitude'].max()) / 2

    # View settings
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=3.6,
        pitch=0
    )

    # Scatterplot layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[longitude, latitude]',
        get_color='color',
        get_radius=20000,  # meters
        pickable=True
    )

    # Show map
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"html": "<b>City:</b> {location}<br/>"
                         "<b>Avg Rank:</b> {Avg Rank}"},
        map_style="mapbox://styles/mapbox/light-v9"
    ))
