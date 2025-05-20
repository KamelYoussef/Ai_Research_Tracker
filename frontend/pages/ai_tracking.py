import streamlit as st
import yaml
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import logout, fetch_param, get_date_today, fetch_response


if 'logged_in' in st.session_state and st.session_state.logged_in:
    pass
else:
    st.switch_page("login.py")

st.set_page_config(
    page_title="AI Investigator",
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

def main():
    # Sidebar buttons
    if st.sidebar.button("Dashboard"):
        st.switch_page("pages/webapp.py")
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()
    if st.sidebar.button("Logout"):
        logout()

    # Fetch parameters
    with open(str(Path(__file__).resolve().parent.parent)+'/data/data.yml', 'r') as file:
        data = yaml.safe_load(file)
    all_locations = data['locations']
    all_products = data['products']
    all_ai_platforms = data['ai_platforms']

    prompts = data['prompts']
    selected_prompt = st.radio("Choose your query:", prompts)
    st.divider()
    col3, col4, col5, col6, col7, col8 = st.columns([4,0.1,4,2,4,2])
    with col4:
        st.write("")
        st.write("")
    with col3:
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

    with col8:
        st.write("")
        st.write("")
        select_all_ai_platforms = st.checkbox("Select All AI Platforms")
    with col7:
        if select_all_ai_platforms:
            st.multiselect("Select AI Platforms", all_ai_platforms, disabled=True)
            ai_platforms_choice = all_ai_platforms
        else:
            ai_platforms_choice = st.multiselect("Select AI Platforms", all_ai_platforms)


    if st.button("Run research"):
        if not selected_locations:
            st.error("Please select at least one location.")
        elif not selected_products:
            st.error("Please select at least one product.")
        elif not ai_platforms_choice:
            st.error("Please select at least one AI platform.")
        else:
            with st.spinner("Fetching data..."):
                # Fetch data for selected AI platforms
                response_data = [
                    fetch_response(platform, selected_locations, selected_products, selected_prompt)
                    for platform in ai_platforms_choice
                ]

                # Check if any response contains an error
                if any("error" in response for response in response_data):
                    st.error("An error occurred while fetching data.")
                else:
                    # Create tabs for each AI platform
                    tabs = st.tabs(ai_platforms_choice)

                    # Iterate through the tabs and display the corresponding responses
                    for tab, platform in zip(tabs, ai_platforms_choice):
                        with tab:
                            # Filter responses for the current platform
                            filtered_responses = [
                                response for response in response_data
                                if response.get("ai_platform") == platform
                            ]

                            if filtered_responses:
                                for ai_response, insight in zip(filtered_responses[0]["ai_responses"],
                                                                filtered_responses[0]["results"]):
                                    product = insight.get("product", "Unknown Product")
                                    location = insight.get("location", "Unknown Location")
                                    total_count = insight.get("total_count", "N/A")
                                    rank = rank if (rank := insight.get("rank")) is not None else "N/A"

                                    # Use an expander to display details
                                    with st.expander(
                                            f"{location} | {product} | Appearance: {bool(total_count)} | Position : {rank}"
                                    ):
                                        st.write(ai_response)
                            else:
                                st.warning(f"No responses available.")


if __name__ == "__main__":
    main()
