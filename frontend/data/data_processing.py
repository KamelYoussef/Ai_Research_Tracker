from data.fetch_utils import download_data, fetch_param
import streamlit as st
import pandas as pd


def ai_platforms_score(month, competitor_flag):
    df = download_data(month, competitor_flag)[2]
    n_locations, n_products, n_ai_platforms = df["location"].nunique(), df["product"].nunique(), df["ai_platform"].nunique()
    ai_scores = df.groupby("ai_platform")[["Total Count"]].sum().reset_index()
    ai_scores["Total Count"] = (ai_scores["Total Count"] / (n_locations * n_products) / 4 * 100).round(1)
    return ai_scores.set_index('ai_platform')['Total Count'].to_dict()


def keywords_data(month, competitor_flag):
    # Process the data
    df = download_data(month, competitor_flag)[0]

    ai_platforms = df["ai_platform"].unique()
    df["Total Count"] = (df["Total Count"] / len(fetch_param(month, competitor_flag)[0]) / 4 * 100).astype(float).round(2)
    x = df.groupby(["ai_platform", "product"])[["Total Count"]].sum()

    keywords_presence = {}
    for platform in ai_platforms:
        keywords_presence[platform.capitalize()] = x.loc[platform.upper()]["Total Count"].tolist()

    return keywords_presence


@st.cache_data
def fetch_and_process_data(month, competitor_flag):
    locations, keywords, models = fetch_param(month, competitor_flag)
    scores = ai_platforms_score(month, competitor_flag)
    locations_data_df = locations_data(month, competitor_flag)
    return locations, keywords, models, scores, locations_data_df


def locations_data(month, competitor_flag):
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
    df = download_data(month, competitor_flag)[1]

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


def top_locations(month, competitor_flag):
    df = download_data(month, competitor_flag)[1]
    ranking_df = df.groupby("location")[["Total Count"]].sum().reset_index().sort_values(by='Total Count', ascending=False)
    return ranking_df['location'].tolist()


def top_low_keywords(month, competitor_flag):
    df = download_data(month, competitor_flag)[0]
    ranking_df = df.groupby("product")[["Total Count"]].sum().reset_index().sort_values(by='Total Count', ascending=False)
    return ranking_df.iloc[0]["product"], ranking_df.iloc[-1]["product"]


def stats_by_location(month: int, selected_location: str, competitor_flag) -> pd.DataFrame:
    """
    Generate a pivot table showing statistics by product and AI platform for a given location and month.

    Args:
        month (int): The month for which data is being analyzed (1-12).
        selected_location (str): The location to filter the data.

    Returns:
        pd.DataFrame: A pivot table with products as rows, AI platforms as columns, and normalized total counts as values.
    """
    # Process and pivot the data
    df = download_data(month, competitor_flag)[2]

    # Validate inputs
    if selected_location not in df["location"].unique():
        raise ValueError(f"Invalid location: {selected_location}. Please select a valid location.")

    # Filter the data for the selected location
    filtered_df = df[df["location"] == selected_location].copy()

    # Normalize and round the "Total Count" column
    filtered_df.loc[:, "Total Count"] = (
        (filtered_df["Total Count"] / 4 * 100)
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


def convert_df(df):
    """Converts a pandas dataframe to a CSV string."""
    return df.to_csv(index=False)


def get_location_scores(month, locations, competitor_flag):
    scores = []

    for loc in locations:
        # Call your function to get data for this location
        data = stats_by_location(month, loc, competitor_flag)

        # Convert data to DataFrame
        df = pd.DataFrame(data)

        # Calculate total sum and count of numeric values
        total_sum = df.select_dtypes(include='number').sum().sum()
        total_count = df.select_dtypes(include='number').count().sum()

        # Calculate average score safely
        avg_score = round(float(total_sum / total_count), 1) if total_count > 0 else 0

        # Collect result
        scores.append({"location": loc, "score": avg_score})

    # Return DataFrame with location and score
    return pd.DataFrame(scores)