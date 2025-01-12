import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import plotly.graph_objects as go
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import select_month, get_ai_total_score, \
    plot_pie_chart, plot_bar_chart, fetch_and_process_data, keywords_data, top_locations, top_low_keywords, \
    stats_by_location, download_data, convert_df, logout, process_and_pivot_data


if 'logged_in' in st.session_state and st.session_state.logged_in:
    pass
else:
    st.switch_page("login.py")

# Set Streamlit page configuration
st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

header_col1, header_col2 = st.columns([2, 1])
with header_col1:
    competitor_flags = {
        "Western Financial": "total_count",
        "Co-operators": "competitor_1",
        "Westland": "competitor_2",
        "Square One": "competitor_3",
    }
    choice = st.selectbox("Choose an option:", list(competitor_flags.keys()))
with header_col2:
    # get the month to generate the monthly report
    month = select_month()

header_col3, header_col4 = st.columns([8, 1])
with header_col4:
    st.download_button(
        label="Export data",
        data=convert_df(download_data(month, competitor_flags[choice])[2]),
        file_name="all_data.csv",
        mime="text/csv"
    )

# Display Total Score in a header
st.markdown(f"<h2 style='text-align: center;'>✨ AI Score = {get_ai_total_score(month)}</h2>",
            unsafe_allow_html=True)

st.divider()

# Display ai_platforms scores and graphs
locations, keywords, models, scores, locations_data_df = fetch_and_process_data(month, competitor_flags[choice])
keywords_presence = keywords_data(month, competitor_flags[choice])

columns = st.columns(3)
for model, score, locations_showed, locations_no_results, keyword_presence, column in zip(
        models, scores.values(), locations_data_df["Locations Showed"], locations_data_df["Locations No Results"],
        keywords_presence.values(), columns
):
    with column:
        st.markdown(f"<h6 style='text-align: center;'>{model} Score = {score}</h2>", unsafe_allow_html=True)

        # Pie chart for Locations Showed vs No Results
        pie_data = pd.DataFrame({
            "Category": ["Locations Showed", "Locations No Results"],
            "Count": [locations_showed, locations_no_results],
        })
        st.plotly_chart(plot_pie_chart(pie_data), key=f"pie_chart_{model}", use_container_width=True)

        # Bar chart for Keyword Presence
        bar_data = pd.DataFrame({
            "Keyword": keywords,
            "Presence": keyword_presence,
        })
        st.plotly_chart(plot_bar_chart(bar_data), key=f"bar_chart_{model}", use_container_width=True)

st.divider()

# Lists for Top Locations and Opportunities
col4, col5, col6 = st.columns(3)
with col4:
    st.write("**Top-Performing Locations:** 🚀")
    st.write("\n".join(f"- {location}" for location in top_locations(month, competitor_flags[choice])[:5]))
with col5:
    st.write("**Areas for Opportunity:** 📈")
    st.write("\n".join(f"- {location}" for location in list(reversed(top_locations(month, competitor_flags[choice])[-5:]))))
with col6:
    st.write("**Keywords Insight:**")
    top_keyword, low_keyword = top_low_keywords(month, competitor_flags[choice])
    st.write(f"- Top keyword: {top_keyword}\n- Low keyword: {low_keyword}")

st.divider()

# Stats by location
col7, col8 = st.columns([3, 5])
with col7:
    search_query = st.selectbox("**Search Locations**", options=locations, index=0)

    st.write(f"% of times {search_query} showed in search")
    data = stats_by_location(month, search_query, competitor_flags[choice])
    df = pd.DataFrame(data)

    st.dataframe(df, hide_index=True, use_container_width=True)

with col8:
    with st.container():  # Manage space using a container
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

        # Display the radar chart
        st.plotly_chart(fig, use_container_width=True)

if st.sidebar.button("AI Investigator"):
    st.switch_page("pages/ai_tracking.py")

if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()

if st.sidebar.button("Logout"):
    logout()