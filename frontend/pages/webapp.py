import streamlit as st
import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import select_month, get_ai_total_score, download_data, logout, process_and_pivot_data,\
    validate_token, get_avg_rank, get_avg_rank_by_platform, get_ai_scores_full_year, get_ranks_full_year, format_month,\
    get_sources, dict_to_text, get_avg_sentiment, get_sentiments_full_year, get_avg_sentiment_by_platform
from components.charts import plot_pie_chart, plot_bar_chart, create_radar_chart, plot_ai_scores_chart, plot_rank_chart, \
    display_map_with_score_colors, plot_sentiment_chart
from data.data_processing import keywords_data, top_locations, top_low_keywords, convert_df, stats_by_location,\
    fetch_and_process_data, get_location_scores
from components.header import render_tooltip_heading
from streamlit_option_menu import option_menu

# Check the login state
if 'logged_in' in st.session_state and validate_token():
    pass
else:
    st.switch_page("login.py")

# Set Streamlit page configuration
st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

font_css = """
<style>
   button[data-baseweb="tab"] {
   font-size: 24px;
   margin: 0;
   width: 100%;
   }
</style>
"""
st.write(font_css, unsafe_allow_html=True)

header_col1, header_col2, _ ,header_col3 = st.columns([1.5, 1.5, 2, 2])
# Choose company or one of the competitors
with header_col1:
    competitor_flags = {
        "Western Financial": "total_count",
        "Co-operators": "competitor_1",
        "Westland": "competitor_2",
        "Brokerlink": "competitor_3",
    }
    choice = st.selectbox(" ", list(competitor_flags.keys()))

with header_col2:
    view_option = st.selectbox(" ",["Locations", "Provinces"])

is_city = view_option == "Locations"

with header_col3:
    # get the month to generate the monthly report
    month = select_month()

# Download button for raw data
header_col4, _, header_col5 = st.columns([7,2.5,1.5])
with header_col4:
    st.markdown(
        f"<h3 style='text-align: left;'>Overview - {format_month(month)}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h7 style='text-align: left;'> Here’s a quick summary of your brand’s performance this month across \
    all three AI platforms, multiple locations, and five keywords showing how often it appeared and where it ranked. </h7>", unsafe_allow_html=True)
with header_col5:
    st.download_button(
        label="Export data",
        data=convert_df(download_data(month, competitor_flags[choice], is_city)[2]),
        file_name="all_data.csv",
        mime="text/csv",
        use_container_width=True
    )

col1, col2, col3 = st.columns(3)
with col1:
    # Display Total Score in a header
    render_tooltip_heading("Visibility score", "How often your brand appeared in AI-generated responses this month \
    across 3 AI platforms. \n [Based on 1,680 prompts run weekly (4 runs per month), totaling 6,720 prompts across all \
    locations and keywords].")

    st.markdown(
        f"<h1 style='text-align: left; margin-top: -30px;'>"
        f"{get_ai_total_score(month, competitor_flags[choice], is_city)} %"
        f"</h1>",
        unsafe_allow_html=True)

    plot_ai_scores_chart(get_ai_scores_full_year(month, competitor_flags[choice], is_city))

with col2:
    render_tooltip_heading("Average position", "Average position where your brand appeared in AI-generated responses this\
    month. \nInstances where your brand was not mentioned are excluded from the average.")
    st.markdown(
        f"<h1 style='text-align: left; margin-top: -30px;'>"
        f"{get_avg_rank(month, competitor_flags[choice], is_city)}</h1>",
        unsafe_allow_html=True)
    plot_rank_chart(get_ranks_full_year(month, competitor_flags[choice], is_city))

with col3:
    render_tooltip_heading("Average sentiment", "Average sentiment (scale: -1 to 1) based on AI-generated responses \
    this month. Responses that did not mention your brand are excluded from the calculation.")
    avg_sentiment = get_avg_sentiment(month, competitor_flags[choice], is_city)
    if avg_sentiment != "N/A":
        if avg_sentiment >= 0.6: sentiment_label = "Very Positive 😀"
        elif avg_sentiment >= 0.25: sentiment_label = "Positive 🙂"
        elif avg_sentiment <= -0.6: sentiment_label = "Very Negative 😡"
        elif avg_sentiment <= -0.25: sentiment_label = "Negative 😕"
        else: sentiment_label = "Neutral 😐"
    else : sentiment_label ="N/A"
    st.markdown(
        f"""
            <div style="display: inline-flex; align-items: center; margin-top: -30px;">
                <h1 style="margin: 0;">{avg_sentiment}</h1>
                <span style="font-size: 15px; margin-left: -15px;white-space: nowrap;">({sentiment_label})</span>
            </div>
            """,
        unsafe_allow_html=True
    )

    plot_sentiment_chart(get_sentiments_full_year(month, competitor_flags[choice], is_city))

# Display ai_platforms scores and graphs
locations, keywords, models, scores, locations_data_df = fetch_and_process_data(month, competitor_flags[choice], is_city)
keywords_presence = keywords_data(month, competitor_flags[choice], is_city)

if is_city:
    st.markdown(f"<h3 style='text-align: left;'>Visibility score by location</h3>", unsafe_allow_html=True)

    display_map_with_score_colors(get_location_scores(month, locations, competitor_flags[choice], is_city))
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 30px; height: 20px; background-color: rgb(255, 0, 0);"></div> Low Score
            <div style="width: 30px; height: 20px; background-color: rgb(0, 255, 0);"></div> High Score
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Lists for Top Locations and Opportunities
col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(f"<h4 style='text-align: left;'>Top-Performing Locations: 🚀</h4>", unsafe_allow_html=True)
    st.write("\n".join(f"- {location}" for location in top_locations(month, competitor_flags[choice], is_city)[:5]))
with col5:
    st.markdown(f"<h4 style='text-align: left;'>Areas for Opportunity: 🎯</h4>", unsafe_allow_html=True)
    st.write("\n".join(f"- {location}" for location in list(reversed(top_locations(month, competitor_flags[choice], is_city)[-5:]))))
with col6:
    st.markdown(f"<h4 style='text-align: left;'>Keywords Insight:</h4>", unsafe_allow_html=True)
    top_keyword, low_keyword = top_low_keywords(month, competitor_flags[choice], is_city)
    st.write(f"- Top keyword: {top_keyword}\n- Low keyword: {low_keyword}")

st.divider()

st.markdown(f"<h3 style='text-align: left;'>Analysis by Platform</h3>", unsafe_allow_html=True)

columns = st.columns(len(models))
for model, score, locations_showed, locations_no_results, keyword_presence, column in zip(
        models, scores.values(), locations_data_df["Locations Showed"], locations_data_df["Locations No Results"],
        keywords_presence.values(), columns
):
    with column:
        st.markdown(f"<h4 style='text-align: left;'>{model}</h4>", unsafe_allow_html=True)
        st.markdown(f"<h6 style='text-align: left; margin-top: -10px;'>"
                    f"Visibility score : {score} % "
                    f"</h6>", unsafe_allow_html=True)
        st.markdown(f"<h6 style='text-align: left; margin-top: -10px;'>"
                    f"Average position : {get_avg_rank_by_platform(month, model, competitor_flags[choice], is_city)} "
                    f"</h6>", unsafe_allow_html=True)
        st.markdown(f"<h6 style='text-align: left; margin-top: -10px;'>"
                    f"Average sentiment : {get_avg_sentiment_by_platform(month, model, competitor_flags[choice], is_city)} "
                    f"</h6>", unsafe_allow_html=True)

        # Bar chart for Keyword Presence
        bar_data = pd.DataFrame({
            "Keyword": keywords,
            "Visibility score": keyword_presence,
        })
        st.plotly_chart(plot_bar_chart(bar_data), key=f"bar_chart_{model}", use_container_width=True)

        # Pie chart for Locations Showed vs No Results
        pie_data = pd.DataFrame({
            "Category": ["Showed", "No Results"],
            "Count": [locations_showed, locations_no_results],
        })
        st.plotly_chart(plot_pie_chart(pie_data), key=f"pie_chart_{model}", use_container_width=True)

with st.expander("How to interpret this pie chart ? ℹ️"):
    st.markdown("""
    This chart presents data **aggregated by location**, showing how many locations your brand appeared in across AI-generated responses this month.

    It summarizes visibility using **6,720 prompts total**, which come from running **1,680 prompts weekly (4 runs per month)** across multiple keywords and locations.

    - **“Locations Showed”**: The brand showed up **at least once** in AI results for that location — even if only for one keyword in one prompt.
    - **“Locations Not Showed”**: The brand **did not appear even once** for any keyword in that location across all prompts for the month.

    ⚠️ **Locations in “Not Showed” should be flagged.** These represent areas with **zero brand visibility** in AI-generated answers — a potential risk that may require further investigation or action.
    """)

st.divider()

st.markdown(f"<h3 style='text-align: left;'>Detailed Analysis</h3>", unsafe_allow_html=True)
# Stats by location
col7, col8 = st.columns([3, 5])
with col7:
    search_query = st.selectbox("**Search Locations**", options=locations, index=0)

    data = stats_by_location(month, search_query, competitor_flags[choice], is_city)
    df = pd.DataFrame(data)

    total_sum = df.select_dtypes(include='number').sum().sum()
    total_count = df.select_dtypes(include='number').count().sum()

    st.markdown(f"<h6 style='text-align: left;'>"
                f"Visibility score : {round(float(total_sum / total_count),1)} % "
                f"</h6>", unsafe_allow_html=True)
    st.write(f"{search_query}'s visibility score across AI platforms")
    st.dataframe(df, hide_index=True, use_container_width=True)

with col8:
    with st.container():
        # Create and display the radar chart
        radar_chart = create_radar_chart(df)
        st.plotly_chart(radar_chart, use_container_width=True)

st.divider()

st.markdown(f"<h3 style='text-align: left;'>Citations</h3>", unsafe_allow_html=True)
st.markdown(f"<h7 style='text-align: left;'> These are sources used by the AI platforms in their responses this month.</h7>", unsafe_allow_html=True)

tabs = st.tabs(models)
for tab, model in zip(tabs, models):
    with tab:
        st.write(dict_to_text(get_sources(month, model)))

# Sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",  # Optional
        options=["Tracker", "Investigator", "Maps", "Clear Cache", "Logout", "Settings"],
        icons=["eye", "search", "geo-alt", "arrow-clockwise", "box-arrow-left", "gear"],  # Optional icons
        menu_icon="list"
    )

# Actions based on selection
if selected == "Investigator":
    st.switch_page("pages/ai_tracking.py")

elif selected == "Maps":
    st.switch_page("pages/maps.py")

elif selected == "Clear Cache":
    st.cache_data.clear()
    st.success("Cache cleared!")

elif selected == "Logout":
    logout()

elif selected == "Settings":
    st.switch_page("pages/user_management.py")

with st.sidebar:
    st.markdown("""
    <style>
    /* Make sidebar container relative and reserve footer space */
    div[data-testid="stSidebar"] > div:nth-child(1) {
        position: relative;
        padding-bottom: 4rem; /* Reserve space for footer */
    }

    /* Add padding below the navigation menu */
    [data-testid="stSidebarNav"] {
        padding-bottom: 2rem;
    }

    /* Absolutely position the footer right under the nav, pinned to sidebar bottom */
    [data-testid="stSidebarNav"] + div {
        position: absolute;
        bottom: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    </style>

    <div>
      <p style="margin: 0; font-size: 0.8rem; color: #888;">
        © 2025 Presence AI
      </p>
      <p style="margin: 0; font-size: 0.8rem; color: #888;">
        A portion of the revenue is donated to support Palestine 🇵🇸
      </p>
    </div>
    """, unsafe_allow_html=True)
