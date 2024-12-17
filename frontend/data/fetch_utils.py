import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st
import seaborn as sns
from datetime import datetime
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the FastAPI server URL
FASTAPI_URL = os.getenv("FASTAPI_URL")
#FASTAPI_URL = "http://localhost:8000"


# Utility: Fetch data from the API
def fetch_data(endpoint: str, month: str):
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
        return response.json()
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
    data = fetch_data(endpoint, month).get("aggregated_data", [])
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


def get_date_today():
    current_year = datetime.today().year
    current_month = datetime.today().month
    return f"{current_year}{str(current_month).zfill(2)}"


def select_month():
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
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_year = st.selectbox("Select Year", years, index=years.index(str(current_year)))
    with col2:
        selected_month_name = st.selectbox("Select Month", month_names, index=current_month - 1)

    # Convert the selected month name to its corresponding number (01-12)
    selected_month = month_names.index(selected_month_name) + 1
    selected_month_str = f"{selected_year}{str(selected_month).zfill(2)}"

    # Return the selected month string and search button status
    return selected_month_str


def fetch_tracking_data(endpoint, ai_platform):
    """
    Fetch tracking data from the FastAPI endpoint.
    """
    url = f"{FASTAPI_URL}/{endpoint}/{ai_platform}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}


def display_ai_tracking():
    """
    Display AI tracking results for a specific month.
    """

    platforms = ["CHATGPT", "PERPLEXITY"]
    for ai_platform in platforms:
        with st.spinner(f"Fetching data for {ai_platform}..."):
            data = fetch_tracking_data("submit_query_with_default", ai_platform)

        if data["status"] != "success":
            st.error(f"Error fetching data for {ai_platform}: {data.get('message', 'Unknown error')}")
            continue

        results = data["data"]
        st.markdown(f"### Results for {ai_platform}")

        if not results:
            st.warning(f"No results found for {ai_platform}.")
            continue

        # Display results in a table
        df = pd.DataFrame(results)
        st.dataframe(df)

        # Optional: Add visualizations
        st.markdown("#### Visualizations")
        count_by_location = pd.DataFrame(results).groupby("location")["total_count"].sum()
        st.bar_chart(count_by_location)


def get_ai_total_score(month):
    if fetch_data("score_ai", month):
        return fetch_data("score_ai", month).get("score_ai", [])


def ai_platforms_score(month):
    df = download_data(month)[2]
    n_locations, n_products, n_ai_platforms = df["location"].nunique(), df["product"].nunique(), df["ai_platform"].nunique()
    ai_scores = df.groupby("ai_platform")[["Total Count"]].sum().reset_index()
    ai_scores["Total Count"] = (ai_scores["Total Count"] / (n_locations * n_products) / days_in_month(month) * 100).astype(int)
    return ai_scores.set_index('ai_platform')['Total Count'].to_dict()


def fetch_param(month):
    df = download_data(month)[2]
    locations = df["location"].unique().tolist()
    products = df["product"].unique().tolist()
    ai_platforms = df["ai_platform"].unique().tolist()
    return locations, products, ai_platforms


def locations_data(month):
    """
    Calculate the number of locations that showed results and the number of locations with no results
    for each AI platform, ensuring the output lists match the total number of locations.
    If no results, return 0 for missing platforms.

    Parameters:
    month (str): A string in the format 'YYYYMM' representing the target month.

    Returns:
    dict: A dictionary with keys "Locations Showed" and "Locations No Results",
          where values are lists of counts for each AI platform.
    """
    # Process the data
    df = download_data(month)[1]

    # Get the unique ai_platform values
    ai_platforms = df["ai_platform"].unique()

    # Filter for rows where Total Count is greater than 0 (locations with results)
    df_showed = df.loc[df["Total Count"] > 0]

    # Count the number of locations for each AI platform that showed results
    showed_counts = df_showed.groupby("ai_platform")["location"].nunique().to_dict()

    # Count the number of locations for each AI platform that had no results (Total Count <= 0)
    df_no_results = df.loc[df["Total Count"] <= 0]
    no_results_counts = df_no_results.groupby("ai_platform")["location"].nunique().to_dict()

    # Use get() to safely retrieve the count for each AI platform, defaulting to 0 if not found
    locations_showed = [showed_counts.get(platform, 0) for platform in ai_platforms]
    locations_no_results = [no_results_counts.get(platform, 0) for platform in ai_platforms]

    # Return the results as a dictionary
    return {
        "Locations Showed": locations_showed,
        "Locations No Results": locations_no_results,
    }


def days_in_month(input_date):
    """
    Returns the number of days in a given month based on a "YYYYMM" string format.

    Parameters:
    input_date (str): Date in the format "YYYYMM" (e.g., "202412" for December 2024)

    Returns:
    int: Number of days in the month
    """
    # Validate input format
    if len(input_date) != 6 or not input_date.isdigit():
        raise ValueError("Input must be a string in the format 'YYYYMM'")

    # Extract year and month
    year = int(input_date[:4])
    month = int(input_date[4:])

    # Validate month range
    if month < 1 or month > 12:
        raise ValueError("Month must be between 01 and 12")

    # List of days in each month
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Check for February in a leap year
    if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        return 29

    return days_per_month[month - 1]


def plot_pie_chart(data):
    return px.pie(
        data, values="Count", names="Category",
        height=350, hole=0.7,
        color_discrete_sequence=["#1f77b4", "#e377c2"]
    )


def plot_bar_chart(data):
    fig = px.bar(
        data, x="Keyword", y="Presence",
        height=350
    )
    fig.update_layout(
        yaxis=dict(range=[0, 100])
    )
    return fig


@st.cache_data
def fetch_and_process_data(month):
    locations, keywords, models = fetch_param(month)
    scores = ai_platforms_score(month)
    locations_data_df = locations_data(month)
    return locations, keywords, models, scores, locations_data_df


def keywords_data(month):
    # Process the data
    df = download_data(month)[0]

    ai_platforms = df["ai_platform"].unique()
    df["Total Count"] = (df["Total Count"] / len(fetch_param(month)[0]) / days_in_month(month) * 100).astype(float).round(2)
    x = df.groupby(["ai_platform", "product"])[["Total Count"]].sum()

    keywords_presence = {}
    for platform in ai_platforms:
        keywords_presence[platform.capitalize()] = x.loc[platform.upper()]["Total Count"].tolist()

    return keywords_presence


def top_locations(month):
    df = download_data(month)[1]
    ranking_df = df.groupby("location")[["Total Count"]].sum().reset_index().sort_values(by='Total Count', ascending=False)
    return ranking_df['location'].tolist()


def top_low_keywords(month):
    df = download_data(month)[0]
    ranking_df = df.groupby("product")[["Total Count"]].sum().reset_index().sort_values(by='Total Count', ascending=False)
    return ranking_df.iloc[0]["product"], ranking_df.iloc[-1]["product"]


def stats_by_location(month: int, selected_location: str) -> pd.DataFrame:
    """
    Generate a pivot table showing statistics by product and AI platform for a given location and month.

    Args:
        month (int): The month for which data is being analyzed (1-12).
        selected_location (str): The location to filter the data.

    Returns:
        pd.DataFrame: A pivot table with products as rows, AI platforms as columns, and normalized total counts as values.
    """
    # Process and pivot the data
    df = download_data(month)[2]

    # Validate inputs
    if selected_location not in df["location"].unique():
        raise ValueError(f"Invalid location: {selected_location}. Please select a valid location.")

    # Filter the data for the selected location
    filtered_df = df[df["location"] == selected_location].copy()

    # Normalize and round the "Total Count" column
    filtered_df.loc[:, "Total Count"] = (
        (filtered_df["Total Count"] / days_in_month(month) * 100)
        .astype(float)
        .round(0)
    )

    # Pivot the DataFrame
    pivot_df = filtered_df.pivot_table(
        index="product",
        columns="ai_platform",
        values="Total Count",
        fill_value=0
    ).reset_index()

    # Format product names
    INSURANCE_SUFFIX = " Insurance"
    pivot_df["product"] = (pivot_df["product"] + INSURANCE_SUFFIX).str.capitalize()

    return pivot_df


@st.cache_data
def download_data(month):
    df_product = process_and_pivot_data(
        "aggregate_total_by_product",
        ["product", "ai_platform"],
        month
    )
    df_location = process_and_pivot_data(
        "aggregate_total_by_location",
        ["location", "ai_platform"],
        month
    )
    df_all = process_and_pivot_data(
        "aggregate_total_by_product_and_location",
        ["product", "location", "ai_platform"],
        month)
    return df_product, df_location, df_all


def convert_df(df):
    """Converts a pandas dataframe to a CSV string."""
    return df.to_csv(index=False)