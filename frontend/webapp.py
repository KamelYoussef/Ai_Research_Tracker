import streamlit as st
import pandas as pd
import plotly.express as px
from fetch_utils import setup_sidebar, get_ai_total_score

st.set_page_config(
    page_title="Dashboard Tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Layout for Header
header_col1, header_col2 = st.columns([2, 1])
with header_col2:
    month = setup_sidebar()

# Data (mock data for the example)
models = ["ChatGPT", "Gemini", "Perplexity"]
scores = {"ChatGPT": 84, "Gemini": 69, "Perplexity": 75}
total_score = sum(scores.values()) // len(scores)
locations_data = {
    "Locations Showed": [9, 6, 8],
    "Locations No Results": [1, 4, 2],
}
keywords_presence = {
    "ChatGPT": [100, 80, 90, 70, 85],
    "Gemini": [60, 50, 40, 30, 20],
    "Perplexity": [75, 65, 55, 45, 35],
}
keywords = ["Car Insurance", "Home Insurance", "Business Insurance", "Farm Insurance", "Life Insurance"]

# Display Total Score

st.write("""<h2 style='text-align: center;'>AI Score Total = {}</h2>""".format(get_ai_total_score(month)), unsafe_allow_html=True)

# Layout for models in one row
col1, col2, col3 = st.columns(3)

columns = [col1, col2, col3]
for model, score, locations_showed, locations_no_results, keyword_presence, column in zip(
    models, scores.values(), locations_data["Locations Showed"], locations_data["Locations No Results"], keywords_presence.values(), columns
):
    with column:
        st.write(f"{model} Score = {score}")

        pie_data = pd.DataFrame({
            "Category": ["Locations Showed", "Locations No Results"],
            "Count": [locations_showed, locations_no_results],
        })
        pie_chart = px.pie(
            pie_data, values="Count", names="Category",
            height=350,
            color_discrete_sequence=["#1f77b4", "#e377c2"]
        )
        st.plotly_chart(pie_chart, use_container_width=True)

        bar_data = pd.DataFrame({
            "Keyword": keywords,
            "Presence": keyword_presence,
        })
        bar_chart = px.bar(
            bar_data, x="Keyword", y="Presence", title="Keyword Presence",
            height=350
        )
        st.plotly_chart(bar_chart, use_container_width=True)

# Lists for Top Locations and Opportunities
col4, col5 = st.columns(2)
with col4:
    st.write("**Top-Performing Locations:**")
    st.write("- Red Deer\n- Kelowna\n- Winnipeg\n- Oslo")
with col5:
    st.write("**Areas for Opportunity:**")
    st.write("- Georgetown\n- Ottawa\n- Angus\n- Ziplet")

# Keyword Overview Table
st.write("**Keyword Overview**")
keyword_overview_df = pd.DataFrame({
    "Keyword": keywords,
    "% of Times Location Showed in Search": [70, 32, 54, 66, 75],
})
st.table(keyword_overview_df)

# Search Bar
st.text_input("Search Locations")
