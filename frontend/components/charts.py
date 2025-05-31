import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import streamlit as st
import pydeck as pdk
import pandas as pd
import json

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

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('Month:N', sort=month_order, axis=alt.Axis(title='')),
        y=alt.Y('Visibility score:Q', scale=alt.Scale(domain=[0, 100]),axis=alt.Axis(title=''))
    ).properties(
        height=200
    )

    st.altair_chart(chart, use_container_width=True)


def plot_rank_chart(data):
    df = data.reset_index()
    df.columns = ["month", "rank"]
    month_order = df["month"].tolist()

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("month:N", sort=month_order, axis=alt.Axis(title='')),
        y=alt.Y("rank:Q", axis=alt.Axis(title=''), scale=alt.Scale(domain=[df["rank"].max(), 0])),
    ).properties(
        height=200
    )

    st.altair_chart(chart, use_container_width=True)


def display_map_with_score_colors(df_scores):

    # Load location data
    with open("data/geo.json") as f:
        locations = json.load(f)
    df_locations = pd.DataFrame(locations)

    # Merge with scores
    df = df_locations.merge(df_scores, on="location", how="left")
    df['score'] = df['score'].fillna(0)

    # Map to RGB color: blue (low) → red (high)
    def score_to_color(s):
        r = int(s * 255 / 100)
        g = int((1 - s / 100) * 100)
        b = int((1 - s / 100) * 255)
        return [r, g, b, 200]  # Last is alpha

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
        get_radius=30000,
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
    month_order = df["month"].tolist()

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('month:N', sort=month_order, axis=alt.Axis(title='')),
        y=alt.Y('sentiment:Q', scale=alt.Scale(domain=[-1,1]),axis=alt.Axis(title=''))
    ).properties(
        height=200
    )

    st.altair_chart(chart, use_container_width=True)