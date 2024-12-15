import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import *
import requests

st.set_page_config(
    page_title="Query tool",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data
def fetch_data(ai_platform, locations, products):
    api_url = "http://localhost:8000/submit_query_with_ai_platform"
    payload = {
        "ai_platform": ai_platform,
        "locations": locations,
        "products": products
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch data: {e}"}


def main():
    st.title("AI Query Tool")

    # Fetch parameters
    all_locations, all_products, all_ai_platforms = fetch_param(get_date_today())

    col1, col2 = st.columns([4,1])
    # Non-editable search text
    with col1:
        search_text = "'give me the best {keyword} Insurance companies in {location}'"
        st.text_input("Ask AI ", search_text, disabled=True)
    with col2:
        selected_ai_platform = st.selectbox("Select AI Platform", all_ai_platforms)

    # Create columns for the selections
    col3, col4, col5, col6 = st.columns([4,2,4,2])

    with col4:
        st.write("")
        st.write("")
        select_all_locations = st.checkbox("Select All Locations")
    with col3:
        if select_all_locations:
            st.multiselect("Select Locations", all_locations, disabled=True)
            selected_locations = all_locations
        else:
            selected_locations = st.multiselect("Select Locations", all_locations)

    with col6:
        st.write("")
        st.write("")
        select_all_products = st.checkbox("Select All Products")
    with col5:
        if select_all_products:
            st.multiselect("Select Products", all_products, disabled=True)
            selected_products = all_products
        else:
            selected_products = st.multiselect("Select Products", all_products)

    # Fetch data button
    if st.button("Fetch Data"):
        if not selected_locations:
            st.error("Please select at least one location.")
        elif not selected_ai_platform:
            st.error("Please select an AI platform.")
        elif not selected_products:
            st.error("Please select at least one product.")
        else:
            with st.spinner("Fetching data..."):
                # Call the fetch_data function
                response_data = fetch_data(selected_ai_platform, selected_locations, selected_products)

                if "error" in response_data:
                    st.error(response_data["error"])
                else:
                    # Display AI Responses and Insights together in the same expander
                    if "ai_responses" in response_data and "results" in response_data:
                        st.subheader("AI Responses")

                        # Iterate over both ai_responses and results (insights) using zip
                        for ai_response, insight in zip(response_data["ai_responses"], response_data["results"]):
                            # Extract product and location from the insight
                            product = insight.get('product', 'Unknown Product')
                            location = insight.get('location', 'Unknown Location')
                            total_count = insight.get('total_count', 'N/A')

                            # Use product and location in the expander title
                            with st.expander(f"Location: {location} | Keyword: {product} | Total Count: {total_count}"):

                                # Display AI response
                                st.write(ai_response)

                    else:
                        st.write("No AI responses or insights available.")


if __name__ == "__main__":
    main()
