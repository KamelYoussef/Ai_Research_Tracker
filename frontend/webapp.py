import streamlit as st
import pandas as pd
from data.fetch_utils import select_month, get_ai_total_score, \
    plot_pie_chart, plot_bar_chart, fetch_and_process_data, keywords_data, top_locations, top_low_keywords, \
    stats_by_location, download_data, convert_df

# Set Streamlit page configuration
st.set_page_config(
    page_title="Dashboard Tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)

header_col1, header_col2 = st.columns([2, 1])
with header_col2:
    # get the month to generate the monthly report
    month = select_month()

# Display Total Score in a header
st.markdown(f"<h2 style='text-align: center;'>✨ AI Score = {get_ai_total_score(month)}</h2>",
            unsafe_allow_html=True)

st.write("---")

# Display ai_platforms scores and graphs
locations, keywords, models, scores, locations_data_df = fetch_and_process_data(month)
keywords_presence = keywords_data(month)

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

# Stats by location
col7, col8, col9 = st.columns([2, 3, 2])
with col7:
    search_query = st.selectbox("**Search Locations**", options=locations, index=0)

with col8:
    st.write(f"% of times {search_query} showed in search")
    data = stats_by_location(month, search_query)
    df = pd.DataFrame(data)

    st.dataframe(df, hide_index=True, use_container_width=True)

with col9:
    st.write("**Export data to Excel for analysis**")
    download_buttons = [
        {"label": "Products Data", "file_name": "product_data.csv", "data": convert_df(download_data(month)[0])},
        {"label": "Locations Data", "file_name": "location_data.csv", "data": convert_df(download_data(month)[1])},
        {"label": "All Data", "file_name": "all_data.csv", "data": convert_df(download_data(month)[2])}
    ]
    for button in download_buttons:
        st.download_button(
            label=button["label"],
            data=button["data"],
            file_name=button["file_name"],
            mime="text/csv"
        )

