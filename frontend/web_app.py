import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# Define the FastAPI server URL (adjust to your FastAPI app's host and port)
FASTAPI_URL = "http://localhost:8000"  # Replace with the appropriate URL if needed

# Set up custom page configuration
st.set_page_config(
    page_title="Dashboard Tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Reusable function to fetch, display, and plot data
def fetch_and_display_data(endpoint, group_by_label, month):
    """
    Fetch data from the FastAPI endpoint, display it in a table, and plot a bar chart.

    Args:
        endpoint (str): API endpoint to query.
        group_by_label (str): Label for grouping data (e.g., "product" or "location").
        month (str): The month in YYYYMM format.
    """
    try:
        # Make a GET request to the FastAPI endpoint
        query = f"{FASTAPI_URL}/{endpoint}/{month}"
        response = requests.get(query)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json().get("aggregated_data", [])
            if data:
                # Convert to DataFrame for easy display and manipulation
                df = pd.DataFrame(data)

                # Display data as a table
                st.markdown(f"### Aggregated Data Table by {group_by_label.capitalize()}")
                st.dataframe(df)

                # Plotting the data
                st.markdown(f"### Total Count by {group_by_label.capitalize()} (Bar Chart)")

                # Create a bar chart
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.bar(df[group_by_label], df['total_count'], color='mediumseagreen')
                ax.set_xlabel(group_by_label.capitalize())
                ax.set_ylabel('Total Count')
                ax.set_title(f"Total Count by {group_by_label.capitalize()} for {month}")
                plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.warning(f"No data found for {month} ({group_by_label.capitalize()} Aggregation).")
        else:
            st.error(f"Error ({group_by_label.capitalize()} Aggregation): {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred ({group_by_label.capitalize()} Aggregation): {e}")


# Sidebar layout
st.sidebar.title("Dashboard Configuration")
st.sidebar.markdown("Use the controls below to configure the dashboard.")

# User input for the month
month = st.sidebar.text_input("Enter Month (YYYYMM format)", placeholder="E.g., 202401")

# Fetch data button
if st.sidebar.button("Fetch Data"):
    if month:
        # Main layout
        st.title(f"Dashboard Tracking for {month}")
        st.markdown("---")  # Add a horizontal separator

        col1, col2 = st.columns(2)

        # Fetch and display aggregated data by product
        with col1:
            fetch_and_display_data("aggregate_total_by_product", "product", month)

        # Fetch and display aggregated data by location
        with col2:
            fetch_and_display_data("aggregate_total_by_location", "location", month)
    else:
        st.error("Please enter a valid month in the YYYYMM format.")
