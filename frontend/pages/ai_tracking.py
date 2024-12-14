import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import *

st.sidebar.header("AI Tracking Settings")

if st.sidebar.button("Run AI Tracking"):
    display_ai_tracking()

import streamlit as st
import requests


def fetch_data(search_text, ai_platform, locations, product):
    # Mock API call - replace this with your actual API logic
    api_url = "https://example.com/api/data"
    payload = {
        "search_text": search_text,
        "ai_platform": ai_platform,
        "locations": locations,
        "product": product
    }
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch data from the API."}


def main():
    st.title("AI Query Tool")

    # Non-editable search text
    search_text = "Ask AI"
    st.text_input("give me the best {keyword} Insurance companies in {location} ", search_text, disabled=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        # Toggle for AI platforms
        all_ai_platforms = ["OpenAI", "Google", "AWS", "Azure", "Anthropic"]
        select_all_platforms = st.checkbox("Select All AI Platforms")

        if select_all_platforms:
            selected_ai_platforms = all_ai_platforms
            st.write("All AI platforms selected: ", ", ".join(selected_ai_platforms))
        else:
            selected_ai_platforms = st.multiselect("Select AI Platforms", all_ai_platforms)

    with col2:
        # Toggle for locations
        all_locations = ["North America", "Europe", "Asia", "South America", "Africa", "Australia"]
        select_all_locations = st.checkbox("Select All Locations")

        if select_all_locations:
            selected_locations = all_locations
            st.write("All locations selected: ", ", ".join(selected_locations))
        else:
            selected_locations = st.multiselect("Select Locations", all_locations)

    with col3:
        # Toggle for products
        all_products = ["Product A", "Product B", "Product C", "Product D"]
        select_all_products = st.checkbox("Select All Products")

        if select_all_products:
            selected_products = all_products
            st.write("All products selected: ", ", ".join(selected_products))
        else:
            selected_products = st.multiselect("Select Products", all_products)

    # Fetch button
    if st.button("Fetch Data"):
        if not selected_locations:
            st.error("Please select at least one location.")
        elif not selected_ai_platforms:
            st.error("Please select at least one AI platform.")
        elif not selected_products:
            st.error("Please select at least one product.")
        else:
            with st.spinner("Fetching data..."):
                response_data = fetch_data(search_text, selected_ai_platforms, selected_locations, selected_products)

                if "error" in response_data:
                    st.error(response_data["error"])
                else:
                    # Display response text
                    st.subheader("API Response Text")
                    st.write(response_data.get("text", "No text available."))

                    # Display important insights
                    st.subheader("Insights")
                    insights = response_data.get("insights", [])
                    if insights:
                        for insight in insights:
                            st.write(f"- {insight}")
                    else:
                        st.write("No insights available.")


if __name__ == "__main__":
    main()
