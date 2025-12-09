import pandas as pd
import requests
import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from dateutil.relativedelta import relativedelta
from typing import List, Optional

# Load environment variables
load_dotenv()

# Define the FastAPI server URL
FASTAPI_URL = os.getenv("FASTAPI_URL")


# Utility: Fetch data from the API
def fetch_data(endpoint: str, month: str, flag_competitor=None, is_city=True, locations: Optional[List[str]] = None):
    """
    Fetch data from the FastAPI endpoint. (Updated to handle multi-element locations list)

    Args:
        # ... (arguments remain the same)

    Returns:
        list: Data from the API response, or an empty list if an error occurs.
    """
    try:
        # Build base URL (same as before)
        if flag_competitor is not None:
            url = f"{FASTAPI_URL}/{endpoint}/{month}/{flag_competitor}"
        else:
            url = f"{FASTAPI_URL}/{endpoint}/{month}"

        # Start query parameters with is_city
        params = [f"is_city={str(is_city).lower()}"]

        # 🔑 CRITICAL CHANGE: Repeat 'locations=' for each element
        if locations:
            # Create separate query string parameters for each location
            location_params = [f"locations={loc}" for loc in locations]
            params.extend(location_params)  # Add them to the main list of parameters

        # Combine base URL and parameters
        url += "?" + "&".join(
            params)  # This will join everything correctly (e.g., ?is_city=true&locations=Alix&locations=Bolton)

        headers = {
            "Authorization": f"Bearer {st.session_state.get('token')}"
        }

        # print(f"Querying URL: {url}") # Optional: for debugging

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching data from {endpoint} (URL: {url}): {e}")
        return []


# Utility: Process and pivot data
def process_and_pivot_data(endpoint, index_columns, month, competitor_flag, is_city=True, locations: Optional[List[str]] = None):
    """
    Fetch and process data for given index columns, supporting location filtering.

    Args:
        endpoint (str): API endpoint to query.
        index_columns (list): Columns to use as index.
        month (str): Month in YYYYMM format.
        competitor_flag (str): Column to use for pivot values.
        is_city (bool): Whether to filter by city.
        locations (Optional[List[str]]): Specific locations to filter by.

    Returns:
        pd.DataFrame: Pivoted DataFrame with aggregated data or None if empty.
    """
    # Pass the new 'locations' parameter to fetch_data
    data = fetch_data(
        endpoint,
        month,
        is_city=is_city,
        locations=locations
    ).get("aggregated_data", [])

    if data:
        df = pd.DataFrame(data)

        # Handle cases where the required columns are missing (though they shouldn't be based on the aggregation)
        if not all(col in df.columns for col in index_columns + ["day", competitor_flag]):
             st.error("Missing required columns in fetched data.")
             st.stop()
             return None

        df_pivot = df.pivot_table(
            index=index_columns,
            columns="day",
            values=competitor_flag,
            aggfunc="max",
            fill_value=0
        ).reset_index()

        # Calculate 'Total Count' (sum across day columns)
        # Assumes day columns start immediately after index_columns
        df_pivot["Total Count"] = df_pivot.iloc[:, len(index_columns):].sum(axis=1)

        if df_pivot.empty:
            st.error(f"No data available after pivoting.")
            st.stop()
            return None
        else:
            return df_pivot
    else:
        st.error(f"No data available for the selected month/filters.")
        st.stop()
        return None


def select_month():
    """Setup sidebar with year and month selection (default to current month)."""
    # Get the current year and month
    current_year = datetime.today().year
    current_month = datetime.today().month

    # Create a list of years (from 2024 up to current year)
    years = [str(year) for year in range(current_year, 2023, -1)]

    # List of months as full names
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Default month name
    default_month_name = month_names[current_month - 1]

    # Allow the user to select a year and month
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_year = st.selectbox("Select Year", years, index=years.index(str(current_year)))
    with col2:
        selected_month_name = st.selectbox("Select Month", month_names, index=month_names.index(default_month_name))

    # Convert the selected month name to its corresponding number (01-12)
    selected_month = month_names.index(selected_month_name) + 1
    selected_month_str = f"{selected_year}{str(selected_month).zfill(2)}"

    return selected_month_str


def get_date_today():
    """Returns the year and month of the previous month in 'YYYYMM' format."""
    current_year = datetime.today().year
    current_month = datetime.today().month

    # Compute the previous month and adjust the year if needed
    if current_month == 1:
        prev_year = current_year - 1
        prev_month = 12
    else:
        prev_year = current_year
        prev_month = current_month - 1

    return f"{prev_year}{str(prev_month).zfill(2)}"


def get_ai_total_score(month, flag_competitor, is_city=True, locations=None):
    if fetch_data("score_ai", month, flag_competitor, is_city=is_city, locations=locations):
        return fetch_data("score_ai", month, flag_competitor, is_city=is_city, locations=locations).get("score_ai", [])
    else:
        return "N/A"


def fetch_param(month, competitor_flag, is_city=True, locations=None):
    df = download_data(month, competitor_flag, is_city=is_city, locations=locations)[2]
    _locations = df["location"].unique().tolist()
    products = df["product"].unique().tolist()
    ai_platforms = df["ai_platform"].unique().tolist()
    return _locations, products, ai_platforms


@st.cache_data
def download_data(month, competitor_flag, is_city=True, locations=None):
    df_product = process_and_pivot_data(
        "aggregate_total_by_product",
        ["product", "ai_platform"],
        month,
        competitor_flag,
        is_city=is_city,
        locations=locations
    )
    df_location = process_and_pivot_data(
        "aggregate_total_by_location",
        ["location", "ai_platform"],
        month,
        competitor_flag,
        is_city=is_city,
        locations=locations
    )
    df_all = process_and_pivot_data(
        "aggregate_total_by_product_and_location",
        ["product", "location", "ai_platform"],
        month,
        competitor_flag,
        is_city=is_city,
        locations=locations
    )
    return df_product, df_location, df_all


def logout():
    del st.session_state["logged_in"]
    del st.session_state["token"]
    st.session_state.logged_in = False
    st.session_state.token = ""
    st.success("You have logged out!")
    st.switch_page("login.py")


def validate_token():
    """Validates if the stored token is still valid."""
    token = st.session_state.get("token")
    if not token:
        return False

    try:
        # Send a token validation request to FastAPI
        response = requests.get(
            f"{FASTAPI_URL}/validate_token",
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def login():
    """Handles the login functionality."""
    st.header("Presence AI -- Western Financial Group")
    with st.form("login_form", clear_on_submit=True):
        # Username input field
        username = st.text_input("Username")

        # Password input field (hidden)
        password = st.text_input("Password", type="password")

        # Submit button
        login_button = st.form_submit_button("Login", use_container_width=True)

        if login_button:
            with st.spinner("Logging in..."):
                try:
                    # Send login request to FastAPI
                    response = requests.post(
                        f"{FASTAPI_URL}/login",
                        json={"username": username, "password": password},
                    )
                    response.raise_for_status()  # Raise an error for non-2xx status codes

                    # Successful login
                    token = response.json()["access_token"]
                    st.session_state.token = token  # Store token in session
                    st.session_state.logged_in = True  # Set login flag
                    st.success("Login successful!")

                    # Redirect to the main page
                    st.switch_page("pages/webapp.py")
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    # Handle request exceptions
                    st.error(f"An error occurred: {e}")
                except KeyError:
                    # Handle missing token in response
                    st.error("Invalid response from server. Please try again.")


@st.cache_data(show_spinner=False)
def fetch_response(ai_platform, locations, products, prompt):
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


def get_avg_rank(month, flag_competitor, is_city=True, locations = None):
    if flag_competitor == "total_count":
        if fetch_data("rank", month, is_city=is_city, locations=locations):
            if fetch_data("rank", month, is_city=is_city, locations=locations).get("rank", []) is not None:
                return round(float(fetch_data("rank", month, is_city=is_city, locations=locations).get("rank", [])),1)
            else:
                return "N/A"
    else:
        return "N/A"


def get_avg_rank_by_platform(month, ai_platform, flag_competitor, is_city=True, locations=None):
    if flag_competitor == "total_count":
        if fetch_data("rank", month, ai_platform, is_city=is_city, locations=locations):
            if fetch_data("rank", month, ai_platform, is_city=is_city, locations=locations).get("rank", []) is not None:
                return round(float(fetch_data("rank", month,ai_platform, is_city=is_city, locations=locations).get("rank", [])),1)
            else:
                return "N/A"
    else:
        return "N/A"


def get_ai_scores_full_year(from_month, flag_competitor, is_city=True, locations=None):
    year = int(str(from_month)[:4])
    month = int(str(from_month)[4:6])
    end_date = datetime(year, month, 1)

    data = []

    # Last 12 months: from (end_date - 11 months) to end_date
    for i in range(12):
        current_date = end_date - relativedelta(months=11 - i)
        yyyymm = int(current_date.strftime("%Y%m"))
        score = get_ai_total_score(yyyymm, flag_competitor, is_city=is_city, locations=locations)

        data.append({
            "month": current_date.strftime("%b").upper(),  # 'JAN', 'FEB', etc.
            "score": 0 if score == "N/A" else score
        })

    df = pd.DataFrame(data)
    df.set_index("month", inplace=True)
    return df


def get_ranks_full_year(from_month, flag_competitor, is_city=True, locations=None):
    year = int(str(from_month)[:4])
    month = int(str(from_month)[4:6])
    end_date = datetime(year, month, 1)

    data = []

    # Last 12 months: from (end_date - 11 months) to end_date
    for i in range(12):
        current_date = end_date - relativedelta(months=11 - i)
        yyyymm = int(current_date.strftime("%Y%m"))
        score = get_avg_rank(yyyymm, flag_competitor, is_city=is_city, locations=locations)

        data.append({
            "month": current_date.strftime("%b").upper(),  # 'JAN', 'FEB', etc.
            "rank": 0 if score == "N/A" else score
        })

    df = pd.DataFrame(data)
    df.set_index("month", inplace=True)
    return df


def format_month(yyyymm):
    yyyymm_str = str(yyyymm)
    date = datetime.strptime(yyyymm_str, "%Y%m")
    return date.strftime("%B %Y")


def get_sources(month, ai_platform):
    if fetch_data("sources", month, ai_platform):
        return fetch_data("sources", month, ai_platform).get("sources", [])
    else:
        return "N/A"


def dict_to_text(source_dict: dict) -> str:
    """
    Convert a source count dictionary into a human-readable text block.

    Args:
        source_dict: Dictionary of {domain: count}

    Returns:
        A string with each source on a new line like: "domain" – X mentions
    """
    lines = [f'"{source}" – {count} mention{"s" if count != 1 else ""}' for source, count in source_dict.items()]
    return "\n\n".join(lines)


def get_avg_sentiment(month, flag_competitor, is_city=True, locations=None):
    if flag_competitor == "total_count":
        if fetch_data("sentiment", month, is_city=is_city, locations=locations):
            if fetch_data("sentiment", month, is_city=is_city, locations=locations).get("sentiment", []) is not None:
                return round(float(fetch_data("sentiment", month, is_city=is_city, locations=locations).get("sentiment", [])),1)
            else:
                return "N/A"
    else:
        return "N/A"


def get_sentiments_full_year(from_month, flag_competitor, is_city=True, locations=None):
    year = int(str(from_month)[:4])
    month = int(str(from_month)[4:6])
    end_date = datetime(year, month, 1)

    data = []

    # Last 12 months: from (end_date - 11 months) to end_date
    for i in range(12):
        current_date = end_date - relativedelta(months=11 - i)
        yyyymm = int(current_date.strftime("%Y%m"))
        sentiment = get_avg_sentiment(yyyymm, flag_competitor, is_city=is_city, locations=locations)

        data.append({
            "month": current_date.strftime("%b").upper(),  # 'JAN', 'FEB', etc.
            "sentiment": 0 if sentiment == "N/A" else sentiment
        })

    df = pd.DataFrame(data)
    df.set_index("month", inplace=True)
    return df


def get_avg_sentiment_by_platform(month, ai_platform, flag_competitor, is_city=True, locations=None):
    if flag_competitor == "total_count":
        if fetch_data("sentiment", month, ai_platform, is_city=is_city, locations=locations):
            if fetch_data("sentiment", month, ai_platform, is_city=is_city, locations=locations).get("sentiment", []) is not None:
                return round(float(fetch_data("sentiment", month,ai_platform, is_city=is_city, locations=locations).get("sentiment", [])),1)
            else:
                return "N/A"
    else:
        return "N/A"


def maps(month, is_city):
    if fetch_data('aggregate_maps_by_product_and_location', month, is_city=is_city).get("aggregated_data", []):
        # Get unique days and find the latest one (assuming day is a string representing a number)

        data = pd.DataFrame(fetch_data('aggregate_maps_by_product_and_location', month, is_city=is_city).get("aggregated_data", []))
        days = data['day'].unique()

        # Convert days to integers to find max day easily
        max_day = max(map(int, days))
        max_day_str = f"{max_day:02d}"  # zero-padded string

        # Create dict of dfs split by day
        dfs = {day: data[data['day'] == day].reset_index(drop=True) for day in days}

        # Define last_df as the dataframe for the latest day
        last_df = dfs[max_day_str]

        # Rename rank columns to avoid collisions and keep only relevant columns for merging
        for i, (day, df) in enumerate(dfs.items()):
            dfs[day] = df.rename(columns={'rank': f'rank_{i + 1}'})[['location', 'product', f'rank_{i + 1}']]

        # Merge all rank dfs on ['location', 'product'] only (drop 'day' from merge keys)
        dfs_list = list(dfs.values())
        merged_df = dfs_list[0]
        for df in dfs_list[1:]:
            merged_df = pd.merge(merged_df, df, on=['location', 'product'], how='outer')

        # Prepare last_df to contain rating and reviews for latest day, keep only location/product/rating/reviews
        last_df = last_df[['location', 'product', 'rating', 'reviews']]

        # Merge merged_df (with ranks) with last_df (rating/reviews) on location/product
        final_df = pd.merge(merged_df, last_df, on=['location', 'product'], how='left')

        # Calculate average rank across all rank columns, ignoring NaNs
        rank_cols = [col for col in final_df.columns if col.startswith('rank_')]
        final_df['Avg Rank'] = final_df[rank_cols].mean(axis=1, skipna=True)

        # Select and reorder columns, no 'day' column here
        cols = ['location', 'product', 'Avg Rank', 'rating', 'reviews']
        final_df = final_df[cols]

        final_df = final_df.rename(columns={
            'location': 'City',
            'product': 'Keyword',
            'rating': 'Rating',
            'reviews': 'Reviews'
        })

        # Select and reorder columns
        cols = ['City', 'Keyword', 'Avg Rank', 'Rating', 'Reviews']
        final_df = final_df[cols]

        # Fill NaNs if you want
        final_df = final_df.fillna('None')

        # Fill NaNs with 'None' if desired
        final_df = final_df.fillna('None')

        return final_df
    else :
        return None


def get_avg_sentiment_by_location(month, flag_competitor, is_city=True, locations=None):
    if flag_competitor == "total_count":
        if fetch_data("sentiment_by_location", month, is_city=is_city, locations=locations):
            if fetch_data("sentiment_by_location", month, is_city=is_city, locations=locations).get("results", []) is not None:
                return pd.DataFrame(fetch_data("sentiment_by_location", month, is_city=is_city, locations=locations).get("results", []))
            else:
                return None
    else:
        return None


def get_avg_rank_by_location(month, flag_competitor, is_city=True, locations=None):
    if flag_competitor == "total_count":
        if fetch_data("rank_by_location", month, is_city=is_city, locations=locations):
            if fetch_data("rank_by_location", month, is_city=is_city, locations=locations).get("results", []) is not None:
                return pd.DataFrame(fetch_data("rank_by_location", month, is_city=is_city, locations=locations).get("results", []))
            else:
                return None
    else:
        return None