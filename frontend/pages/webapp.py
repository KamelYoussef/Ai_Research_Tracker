import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from streamlit_option_menu import option_menu
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import select_month, get_ai_total_score, download_data, logout, process_and_pivot_data, \
    validate_token, get_avg_rank, get_avg_rank_by_platform, get_ai_scores_full_year, get_ranks_full_year, format_month, \
    get_sources, dict_to_text, get_avg_sentiment, get_sentiments_full_year, get_avg_sentiment_by_platform, \
    get_avg_sentiment_by_location, get_avg_rank_by_location, fetch_data, inject_styles, load_app_config
from components.charts import plot_pie_chart, plot_bar_chart, create_radar_chart, plot_ai_scores_chart, \
    plot_rank_chart, display_map_with_score_colors, plot_sentiment_chart, plot_group_bar
from data.data_processing import keywords_data, top_locations, top_low_keywords, convert_df, stats_by_location, \
    fetch_and_process_data, get_location_scores, transform_value, get_ai_platforms_score_full_year, ai_platforms_score
from components.header import render_tooltip_heading

# -----------------------------Initialisation------------------------------
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
# Set css style
st.write(inject_styles(), unsafe_allow_html=True)

# -----------------------------Page filters------------------------------
header_col1, header_col2, header_col3, _, header_col4 = st.columns([1, 1, 1, 1, 2])
CONFIG = load_app_config()
COMPETITOR_FLAGS = CONFIG["competitor_flags"]
AGGREGATION_LIST = CONFIG["aggregation_list"]

# Choose company or one of the competitors
with header_col1:
    choice = st.selectbox(" ", list(COMPETITOR_FLAGS.keys()))

# Choose locations view or provinces view
with header_col2:
    view_option = st.selectbox(" ", ["Locations", "Provinces"])

is_city = view_option == "Locations"

# Choose top_locations or all_locations view
if is_city:
    with header_col3:
        filter_locations = {
            "All locations": None,
            "Top locations": AGGREGATION_LIST,
        }
        filter_view = st.selectbox(" ", list(filter_locations.keys()))
else:
    filter_locations = {
        "All locations": None
    }
    filter_view = "All locations"

# get the month to generate the monthly report
with header_col4:
    month = select_month()

# -----------------------------Overview------------------------------
header_col4, _, header_col5 = st.columns([7, 2.5, 1.5])
# Title
with header_col4:
    st.header(f"Overview - {format_month(month)}")
    st.write(
        """
        Here’s a quick summary of your brand’s performance this month across 
        all four AI platforms, multiple locations, and five keywords showing 
        how often it appeared and where it ranked.
        """
    )

# Download button for raw data
with header_col5:
    st.download_button(
        label="Export data",
        data=convert_df(download_data(month, COMPETITOR_FLAGS[choice], is_city)[2]),
        file_name="all_data.csv",
        mime="text/csv",
        width='stretch'
    )

col1, col2, col3 = st.columns(3)
# Display Visibility Score
with col1:
    render_tooltip_heading("Visibility Score", "How often your brand appeared in AI-generated responses this month \
    across 4 AI platforms. \n [Based on 2360 prompts run weekly (4 runs per month), totaling 9,440 prompts across all \
    locations and keywords].")

    st.markdown(
        f"<h1 style='text-align: left; margin-top: -30px;'>"
        f"{get_ai_total_score(month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view])} %"
        f"</h1>",
        unsafe_allow_html=True)

    plot_ai_scores_chart(
        get_ai_scores_full_year(
            month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view]
        )
    )

# Display Average Ranking
with col2:
    if COMPETITOR_FLAGS[choice] == "total_count":
        render_tooltip_heading("Average Ranking", "Average position where your brand appeared in AI-generated responses \
        this month. \nInstances where your brand was not mentioned are excluded from the average.")

        st.markdown(
            f"<h1 style='text-align: left; margin-top: -30px;'>"
            f"{get_avg_rank(month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view])}"
            f"</h1>",
            unsafe_allow_html=True)

        plot_rank_chart(
            get_ranks_full_year(
                month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view]
            )
        )

# Display Sentiment Score
with col3:
    if COMPETITOR_FLAGS[choice] == "total_count":
        render_tooltip_heading("Sentiment Score", "Average sentiment based on AI-generated responses \
        this month. Responses that did not mention your brand are excluded from the calculation.")

        avg_sentiment = get_avg_sentiment(month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view])
        avg_sentiment = transform_value(avg_sentiment) if avg_sentiment != "N/A" else "N/A"
        st.markdown(
            f"""<div style="display: inline-flex; align-items: center; margin-top: -30px;">
                    <h1 style="margin: 0;">{avg_sentiment} %</h1>
                </div>
            """,
            unsafe_allow_html=True
        )

        plot_sentiment_chart(
            get_sentiments_full_year(
                month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view]
            )
        )

# -----------------------------Map and Insights------------------------------
locations, keywords, models, scores, locations_data_df = \
    fetch_and_process_data(
        month,
        COMPETITOR_FLAGS[choice],
        is_city,
        locations=filter_locations[filter_view]
    )
# Map
if is_city:
    st.subheader("Visibility Score by Location")
    display_map_with_score_colors(
        get_location_scores(
            month, locations, COMPETITOR_FLAGS[choice], is_city
        )
    )
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 30px; height: 20px; background-color: rgb(255, 0, 0);"></div> Low Score
            <div style="width: 30px; height: 20px; background-color: rgb(0, 255, 0);"></div> High Score
        </div>
        """, unsafe_allow_html=True)

st.divider()
# Get data
keywords_presence = keywords_data(
    month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view]
)
data_rank = get_avg_rank_by_location(
    month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view]
)
data_sentiment = get_avg_sentiment_by_location(
    month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view]
)

# Insights
col4, col5, col6 = st.columns(3)
with col4:
    st.subheader("Top-Performing Locations :")
    st.write(
        "\n".join(f"- {location}" for location in top_locations(
            month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view])[:7]
                  )
    )
with col5:
    st.subheader("Areas for Opportunity :")
    st.write(
        "\n".join(f"- {location}" for location in
                  list(reversed(top_locations(
                      month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view])[-7:])
                       )
                  )
    )
with col6:
    if data_rank is not None and data_sentiment is not None:
        if not (data_rank["avg_rank"].isnull().all() and data_sentiment["avg_sentiment"].isnull().all()):
            st.subheader("Lowest Ranking :")
            st.markdown(
                data_rank.loc[data_rank["avg_rank"].idxmax(), 'location'] + " ➖ " +
                str(data_rank.loc[data_rank["avg_rank"].idxmax(), 'ai_platform']) + " ➖ " +
                str(data_rank.loc[data_rank["avg_rank"].idxmax(), 'avg_rank'])
            )
            st.subheader("Lowest Sentiment Score :")
            st.markdown(
                data_sentiment.loc[data_sentiment["avg_sentiment"].idxmin(), 'location'] + " ➖ " +
                str(data_rank.loc[data_rank["avg_rank"].idxmax(), 'ai_platform']) + " ➖ " +
                str(transform_value(data_sentiment.loc[data_sentiment["avg_sentiment"].idxmin(), 'avg_sentiment'])) +
                " %"
            )

st.divider()
# -----------------------------Analysis by Platform------------------------------
st.header("Analysis by Platform")

ai_platforms_score_full_year = get_ai_platforms_score_full_year(
    month, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view]
)
dfs_by_platform = {
    platform: group.reset_index(drop=True)
    for platform, group in ai_platforms_score_full_year.groupby('AI Platform')
}

columns = st.columns(len(models))
for model, score, locations_showed, locations_no_results, keyword_presence, column in zip(
        models, scores.values(), locations_data_df["Locations Showed"], locations_data_df["Locations No Results"],
        keywords_presence.values(), columns
):
    with column:
        data = dfs_by_platform[model]['score']
        delta = f"{round(float(data.iloc[-1] - data.iloc[-2]), 1)} pts MoM" if len(data) >= 2 else f"{0.0} pts MoM"

        st.subheader(f"{model}")
        st.metric(label="Visibility Score", value=f"{score} %", delta=delta,
                  border=True, chart_data=data, chart_type="area")

        with st.container(horizontal=True):
            if COMPETITOR_FLAGS[choice] == "total_count":
                st.metric(label="Average Ranking",
                          value=f"""{get_avg_rank_by_platform(
                              month, model, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view])
                          }""",
                          border=True
                          )

                model_sentiment = get_avg_sentiment_by_platform(month, model, COMPETITOR_FLAGS[choice], is_city,
                                                                locations=filter_locations[filter_view])
                if model_sentiment != 'N/A' and model_sentiment != 0:
                    model_sentiment = transform_value(model_sentiment)
                st.metric(label="Sentiment Score", value=f"{model_sentiment} %", border=True)

        # Bar chart for Keyword Presence

        bar_data = pd.DataFrame({
            "Keyword": keywords,
            "Visibility score": keyword_presence,
        })
        st.plotly_chart(
            plot_bar_chart(bar_data),
            key=f"bar_chart_{model}",
            width='stretch'
        )
        # Pie chart for Locations Showed vs No Results
        pie_data = pd.DataFrame({
            "Category": ["Showed", "No Results"],
            "Count": [locations_showed, locations_no_results],
        })
        st.plotly_chart(
            plot_pie_chart(pie_data),
            key=f"pie_chart_{model}",
            width='stretch'
        )

with st.expander("How to interpret this pie chart ? ℹ️"):
    st.markdown("""
    This chart presents data **aggregated by location**, showing how many locations your brand appeared in across \
    AI-generated responses this month.
    It summarizes visibility using **9,440 prompts total**, which come from running **2360 prompts weekly \
    (4 runs per month)** across multiple keywords and locations.
    - **“Locations Showed”**: The brand showed up **at least once** in AI results for that location — even if only for \
    one keyword in one prompt.
    - **“Locations Not Showed”**: The brand **did not appear even once** for any keyword in that location across all 
    prompts for the month.
    
    ⚠️ **Locations in “Not Showed” should be flagged.** These represent areas with **zero brand visibility** in 
    AI-generated answers — a potential risk that may require further investigation or action.
    """)

st.divider()
# -----------------------------Stats by location------------------------------
st.subheader("Detailed Analysis")
col7, col8 = st.columns([2, 5])
with col7:
    search_query = st.selectbox("**Search Locations**", options=locations, index=0)
    df = pd.DataFrame(stats_by_location(
        month, search_query, COMPETITOR_FLAGS[choice], is_city, locations=filter_locations[filter_view])
    )

    total_sum = df.select_dtypes(include='number').sum().sum()
    total_count = df.select_dtypes(include='number').count().sum()

    st.metric(label="Visibility score", value=f"{round(float(total_sum / total_count), 1)} % ", border=True)

    horizontal_group = st.container(horizontal=True)
    with horizontal_group:
        if data_rank is not None:
            avg_rank = data_rank[data_rank['location'] == search_query]["avg_rank"].mean()
            if avg_rank is not np.nan:
                st.metric(label="Average Ranking", value=f"{round(float(avg_rank), 1)}", border=True)

        if data_sentiment is not None:
            avg_sentiment = data_sentiment[data_sentiment['location'] == search_query]["avg_sentiment"].mean()
            if avg_sentiment is not np.nan:
                if avg_sentiment != 'N/A':
                    avg_sentiment = transform_value(avg_sentiment)
                    st.metric(label="Sentiment Score", value=f"{round(float(avg_sentiment), 1)} % ", border=True)

with col8:
    with st.container():
        if int(month) < 202510:
            ai_list_bars = ['CHATGPT', 'GEMINI', 'PERPLEXITY']
        else:
            ai_list_bars = ['CHATGPT', 'CLAUDE', 'GEMINI', 'PERPLEXITY']
        df_long = pd.melt(df,
                          id_vars=['product'],
                          value_vars=ai_list_bars,
                          var_name='AI Platform',
                          value_name='Visibility Score (%)'
                          )

    st.plotly_chart(plot_group_bar(df_long), width='stretch')


st.divider()
# ------------------------------Citations-----------------------------
st.subheader("Citations")
st.write("These are sources used by the AI platforms in their responses this month.")

tabs = st.tabs(models)
for tab, model in zip(tabs, models):
    with tab:
        st.write(dict_to_text(get_sources(month, model)))

# ------------------------------Sidebar Menu-----------------------------
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",  # Optional
        options=["Tracker", "Investigator", "Maps", "Clear Cache", "Logout", "Settings"],
        icons=["eye", "search", "geo-alt", "arrow-clockwise", "box-arrow-left", "gear"],
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

st.markdown(
    """
    <style>
        /* Cible la barre latérale uniquement lorsqu'elle est ouverte */
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 250px;
            max-width: 250px;
        }
    </style>
    <style>
    html {
        zoom: 92%;
    }
    </style>
    """,
    unsafe_allow_html=True
)