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
# Function to fetch data from the FastAPI endpoint
def fetch_data_from_api(endpoint, month):
    """
    Fetch data from the FastAPI endpoint.

    Args:
        endpoint (str): API endpoint to query.
        month (str): The month in YYYYMM format.

    Returns:
        list: Aggregated data from the endpoint.
    """
    try:
        query = f"{FASTAPI_URL}/{endpoint}/{month}"
        response = requests.get(query)
        if response.status_code == 200:
            return response.json().get("aggregated_data", [])
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching data: {e}")
        return []

# Function to display data as a table in Streamlit
def display_data_table(data, group_by_label):
    """
    Display data in a table format in Streamlit.

    Args:
        data (list): List of aggregated data.
        group_by_label (str): Label for grouping data (e.g., "product" or "location").
    """
    if data:
        df = pd.DataFrame(data)
        st.markdown(f"### Aggregated Data Table by {group_by_label.capitalize()}")
        st.dataframe(df)
        return df
    else:
        st.warning(f"No data found ({group_by_label.capitalize()} Aggregation).")
        return None

# Function to plot data as a bar chart
def plot_data_bar_chart(df, group_by_label, month):
    """
    Plot data as a bar chart in Streamlit.

    Args:
        df (pd.DataFrame): DataFrame containing aggregated data.
        group_by_label (str): Label for grouping data (e.g., "product" or "location").
        month (str): The month in YYYYMM format.
    """
    if df is not None and not df.empty:
        st.markdown(f"### Total Count by {group_by_label.capitalize()} (Bar Chart)")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(df[group_by_label], df['total_count'], color='mediumseagreen')
        ax.set_xlabel(group_by_label.capitalize())
        ax.set_ylabel('Total Count')
        ax.set_title(f"Total Count by {group_by_label.capitalize()} for {month}")
        plt.xticks(rotation=45)
        st.pyplot(fig)

# Main function to integrate fetch, display, and plot functionalities
def fetch_and_display_data(endpoint, group_by_label, month):
    """
    Fetch data, display it in a table, and plot a bar chart.

    Args:
        endpoint (str): API endpoint to query.
        group_by_label (str): Label for grouping data (e.g., "product" or "location").
        month (str): The month in YYYYMM format.
    """
    data = fetch_data_from_api(endpoint, month)
    df = display_data_table(data, group_by_label)
    plot_data_bar_chart(df, group_by_label, month)


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

        display_data_table(fetch_data_from_api("aggregate_total_by_product_and_location", month), "location x product")

        col1, col2 = st.columns(2)

        # Fetch and display aggregated data by product
        with col1:
            fetch_and_display_data("aggregate_total_by_product", "product", month)

        # Fetch and display aggregated data by location
        with col2:
            fetch_and_display_data("aggregate_total_by_location", "location", month)

    else:
        st.error("Please enter a valid month in the YYYYMM format.")
