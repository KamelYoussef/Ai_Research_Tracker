import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st
import seaborn as sns
from datetime import datetime

# Define the FastAPI server URL
FASTAPI_URL = "http://localhost:8000"


# Utility: Fetch data from the API
def fetch_data(endpoint, month):
    """
    Fetch data from the FastAPI endpoint.

    Args:
        endpoint (str): API endpoint to query.
        month (str): Month in YYYYMM format.

    Returns:
        list: Data from the API response, or an empty list if an error occurs.
    """
    try:
        url = f"{FASTAPI_URL}/{endpoint}/{month}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("aggregated_data", [])
    except requests.RequestException as e:
        st.error(f"Error fetching data from {endpoint}: {e}")
        return []


# Utility: Process and pivot data
def process_and_pivot_data(endpoint, index_columns, month):
    """
    Fetch and process data for given index columns.

    Args:
        endpoint (str): API endpoint to query.
        index_columns (list): Columns to use as index.
        month (str): Month in YYYYMM format.

    Returns:
        pd.DataFrame: Pivoted DataFrame with aggregated data or None if empty.
    """
    data = fetch_data(endpoint, month)
    if data:
        df = pd.DataFrame(data)
        df_pivot = df.pivot_table(
            index=index_columns,
            columns="day",
            values="total_count",
            aggfunc="max",
            fill_value=0
        ).reset_index()
        df_pivot["Total Count"] = df_pivot.iloc[:, len(index_columns):].sum(axis=1)
        return df_pivot
    else:
        st.error(f"No data available for {month}.")
        return None


# Utility: Display table
def display_table(df, title):
    """
    Display data in a table format in Streamlit.

    Args:
        df (pd.DataFrame): DataFrame to display.
        title (str): Title for the table.
    """
    if df is not None and not df.empty:
        st.markdown(f"### {title}")
        st.dataframe(df)
    else:
        st.warning(f"No data available to display for {title}.")


# Utility: Plot bar chart
def plot_bar_chart(df, x_label, title):
    """
    Plot a bar chart using the provided DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing the data.
        x_label (str): Column name to use as x-axis.
        title (str): Title for the chart.
    """
    if df is not None and not df.empty:
        st.markdown(f"### {title}")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=df, x=x_label, y="Total Count", ax=ax, color="mediumseagreen")
        ax.set_xlabel(x_label.capitalize())
        ax.set_ylabel("Total Count")
        ax.set_title(title)
        plt.xticks(rotation=45)
        st.pyplot(fig)


# Dashboard: Display section
def display_section(endpoint, index_columns, x_label, section_title, month):
    """
    Display a section with a table and a bar chart.

    Args:
        endpoint (str): API endpoint to query.
        index_columns (list): Columns to use as index.
        x_label (str): Column to use for the x-axis in the bar chart.
        section_title (str): Title for the section.
        month (str): Month in YYYYMM format.
    """
    df = process_and_pivot_data(endpoint, index_columns, month)
    display_table(df, f"{section_title} Table")
    #plot_bar_chart(df, x_label, f"{section_title} Chart")


# Dashboard: Main display
def display_dashboard(month):
    """
    Display the main dashboard content.

    Args:
        month (str): Month in YYYYMM format.
    """
    st.title(f"Dashboard Tracking for {month}")
    st.markdown("---")

    # Sections
    display_section(
        "aggregate_total_by_product_and_location",
        ["product", "location", "ai_platform"],
        "product",
        "Product x Location Aggregation",
        month
    )
    display_section(
        "aggregate_total_by_product",
        ["product", "ai_platform"],
        "product",
        "Product Aggregation",
        month
    )
    display_section(
        "aggregate_total_by_location",
        ["location", "ai_platform"],
        "location",
        "Location Aggregation",
        month
    )


def setup_sidebar():
    """Setup sidebar with year and month selection."""
    # Get the current year and month
    current_year = datetime.today().year
    current_month = datetime.today().month

    # Create a list of years
    years = [str(year) for year in range(current_year, 2020 - 1, -1)]

    # List of months as full names
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Allow the user to select a year and month
    selected_year = st.sidebar.selectbox("Select Year", years, index=years.index(str(current_year)))
    selected_month_name = st.sidebar.selectbox("Select Month", month_names, index=current_month - 1)

    # Convert the selected month name to its corresponding number (01-12)
    selected_month = month_names.index(selected_month_name) + 1
    selected_month_str = f"{selected_year}{str(selected_month).zfill(2)}"

    return selected_month_str
