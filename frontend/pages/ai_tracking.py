import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import *
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the FastAPI server URL
FASTAPI_URL = os.getenv("FASTAPI_URL")

if 'logged_in' in st.session_state and st.session_state.logged_in:
    pass
else:
    st.switch_page("login.py")

st.set_page_config(
    page_title="AI Investigator",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def fetch_data(ai_platform, locations, products, prompt):
    api_url = f"{FASTAPI_URL}/submit_query_with_ai_platform"
    payload = {
        "ai_platform": ai_platform,
        "locations": locations,
        "products": products,
        "prompt": prompt
    }
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.get('token')}"
        }
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch data: {e}"}


def main():

    if st.sidebar.button("Dashboard"):
        st.switch_page("pages/webapp.py")
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()
    if st.sidebar.button("Logout"):
        logout()

    # Fetch parameters
    all_locations, all_products, all_ai_platforms = fetch_param(get_date_today(), "total_count")

    col1, col2 = st.columns([4,1])
    # Non-editable search text
    with col1:
        prompts = [
            "Give me the best {keyword} insurance in {location}",
            "What are the top {keyword} insurance near {location}?",
            "List the most affordable {keyword} insurance in {location}",
            "Find the highest-rated {keyword} insurance in {location}"
        ]
        selected_prompt = st.radio("Choose your query:", prompts)
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
                response_data = fetch_data(selected_ai_platform, selected_locations, selected_products, selected_prompt)

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
                                #st.write(ai_response)
                                st.code(ai_response, language="markdown")

                    else:
                        st.write("No AI responses or insights available.")


if __name__ == "__main__":
    main()
