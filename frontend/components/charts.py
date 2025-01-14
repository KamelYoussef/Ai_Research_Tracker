import plotly.express as px
import plotly.graph_objects as go


def plot_pie_chart(data):
    return px.pie(
        data, values="Count", names="Category",
        height=350, hole=0.7,
        color_discrete_sequence=["#1f77b4", "#e377c2"]
    )


def plot_bar_chart(data):
    fig = px.bar(
        data, x="Keyword", y="Presence",
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