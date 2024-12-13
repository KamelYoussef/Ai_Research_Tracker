import streamlit as st
import pandas as pd
from data.fetch_utils import setup_sidebar, get_ai_total_score, ai_platforms_score, fetch_param, locations_data, \
    plot_pie_chart, plot_bar_chart, fetch_and_process_data, keywords_data, top_locations, top_low_keywords, \
    stats_by_location, download_data, convert_df

# Set Streamlit page configuration
st.set_page_config(
    page_title="Dashboard Tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Layout for Header
header_col1, header_col2 = st.columns([2, 1])
with header_col2:
    month = setup_sidebar()

locations, keywords, models, scores, locations_data_df = fetch_and_process_data(month)

keywords_presence = keywords_data(month)

# Display Total Score in a header
st.markdown(f"<h2 style='text-align: center;'>✨ AI Score = {get_ai_total_score(month)}</h2>",
            unsafe_allow_html=True)

st.write("---")

# Layout for models in one row with clearer grouping
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

st.write("---")

# Lists for Top Locations and Opportunities
col4, col5, col6 = st.columns(3)
with col4:
    st.write("**Top-Performing Locations:** 🚀")
    st.write("\n".join(f"- {location}" for location in top_locations(month)[:5]))
with col5:
    st.write("**Areas for Opportunity:** 📈")
    st.write("\n".join(f"- {location}" for location in list(reversed(top_locations(month)[-5:]))))
with col6:
    st.write("**Keywords Insight:**")
    top_keyword, low_keyword = top_low_keywords(month)
    st.write(f"- Top keyword: {top_keyword}\n- Low keyword: {low_keyword}")

st.write("---")

col7, col8, col9 = st.columns([2, 3, 2])
with col7:
    search_query = st.selectbox("**Search Locations**", options=locations, index=0)

with col8:
    st.write(f"% of times {search_query} showed in search")
    data = stats_by_location(month, search_query)
    df = pd.DataFrame(data)

    st.dataframe(df, hide_index=True, use_container_width=True)

with col9:
    st.write("Export data to Execl for analysis")
    st.download_button(
        label="Products Data",
        data=convert_df(download_data(month)[0]),
        file_name="product_data.csv",
        mime="text/csv"
    )

    # Button for downloading df_location
    st.download_button(
        label="Locations Data",
        data=convert_df(download_data(month)[1]),
        file_name="location_data.csv",
        mime="text/csv"
    )

    # Button for downloading df_all
    st.download_button(
        label="All Data",
        data=convert_df(download_data(month)[2]),
        file_name="all_data.csv",
        mime="text/csv"
    )

