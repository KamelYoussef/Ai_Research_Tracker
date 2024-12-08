import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st
import seaborn as sns

# Define the FastAPI server URL (you can parameterize this if needed)
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

# Utility: Display data as a table in Streamlit
def display_table(data, label):
    """
    Display data in a table format in Streamlit.

    Args:
        data (list): List of aggregated data.
        label (str): Label for grouping data.

    Returns:
        pd.DataFrame: The DataFrame of the displayed data.
    """
    if data:
        df = pd.DataFrame(data)
        st.markdown(f"### Aggregated Data Table by {label.capitalize()}")
        st.dataframe(df)
        return df
    else:
        st.warning(f"No data found for {label.capitalize()}.")
        return None

# Utility: Plot bar chart in Streamlit
def plot_bar_chart(df, label, month):
    """
    Plot data as a bar chart in Streamlit.

    Args:
        df (pd.DataFrame): DataFrame containing aggregated data.
        label (str): Label for grouping data.
        month (str): The month in YYYYMM format.
    """
    if df is not None and not df.empty:
        st.markdown(f"### Total Count by {label.capitalize()} (Bar Chart)")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(df[label], df["total_count"], color="mediumseagreen")
        ax.set_xlabel(label.capitalize())
        ax.set_ylabel("Total Count")
        ax.set_title(f"Total Count by {label.capitalize()} for {month}")
        plt.xticks(rotation=45)
        st.pyplot(fig)

# Core: Fetch, display, and plot data
def render_data(endpoint, label, month):
    """
    Fetch, display, and plot data from a specific API endpoint.

    Args:
        endpoint (str): API endpoint to query.
        label (str): Label for grouping data.
        month (str): The month in YYYYMM format.
    """
    data = fetch_data(endpoint, month)
    df = display_table(data, label)


def process_combined_data(month):
    """Fetch and process the combined data by product and location."""
    combined_data = fetch_data("aggregate_total_by_product_and_location", month)
    if combined_data:
        df = pd.DataFrame(combined_data)
        df_pivot = df.pivot_table(
            index=['product', 'location'],
            columns='day',
            values='total_count',
            aggfunc='sum',  # In case there are duplicate values for the same product-location-day
            fill_value=0  # Fill NaN values with 0
        )
        df_pivot.reset_index(inplace=True)
        df_pivot['Total Count'] = df_pivot.iloc[:, 2:].sum(axis=1)  # Adding total count column
        return df_pivot
    else:
        st.error("No data available for the selected month.")
        return None


def display_dashboard(month):
    """Display the main dashboard content."""
    st.title(f"Dashboard Tracking for {month}")
    st.markdown("---")  # Horizontal separator

    # Location x Product Aggregation
    st.subheader("Location x Product Aggregation")
    df_pivot = process_combined_data(month)
    if df_pivot is not None:
        st.write(df_pivot)
        plot_bar_chart(df_pivot)

    # Separate buttons for showing product or location-specific data
    st.sidebar.markdown("---")  # Sidebar separator

    # Product Aggregation
    st.subheader("Product Aggregation")
    render_data("aggregate_total_by_product", "product", month)

    # Location Aggregation
    st.subheader("Location Aggregation")
    render_data("aggregate_total_by_location", "location", month)


def setup_sidebar():
    """Set up the sidebar with controls for the user."""
    st.sidebar.title("Dashboard Configuration")
    st.sidebar.markdown("Use the controls below to configure the dashboard.")
    return st.sidebar.text_input("Enter Month (YYYYMM format)", placeholder="E.g., 202412")


def plot_bar_chart(df_pivot):
    """Plot a bar chart based on the pivot table."""
    # Melt the dataframe without Total Count column
    df_melted = df_pivot.drop(columns='Total Count').melt(id_vars=['product', 'location'],
                                                          var_name='Day', value_name='Total Count')

    # Merge the 'Total Count' column back to the melted dataframe
    df_melted['Total Count'] = df_pivot['Total Count'].repeat(df_pivot.shape[1] - 2).reset_index(drop=True)

    # Use seaborn for styling and plotting
    plt.figure(figsize=(10, 6))
    sns.barplot(x='product', y='Total Count', hue='Day', data=df_melted, ci=None)

    plt.title('Total Count by Product and Day')
    plt.xlabel('Product')
    plt.ylabel('Total Count')
    st.pyplot(plt)
