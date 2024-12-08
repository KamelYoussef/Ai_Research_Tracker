import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# Define the FastAPI server URL (adjust to your FastAPI app's host and port)
FASTAPI_URL = "http://localhost:8000"  # Replace with the appropriate URL if needed

# Streamlit app layout
st.title("Dashboard Tracking")

# Input for the month
month = st.text_input("Enter Month (YYYYMM format)")

# Fetch data when the user submits the month
if month:
    try:
        # Make a GET request to the FastAPI aggregate_by_product endpoint
        query = f"{FASTAPI_URL}/aggregate_total_by_product/{month}"
        response = requests.get(query)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json().get("aggregated_data", [])
            if data:
                # Convert to DataFrame for easy display and manipulation
                df = pd.DataFrame(data)

                # Display data as a table
                st.subheader("Aggregated Data Table")
                st.dataframe(df)

                # Plotting the data
                st.subheader("Total Count by Product (Bar Chart)")

                # Create a bar chart
                fig, ax = plt.subplots()
                ax.bar(df['product'], df['total_count'], color='skyblue')
                ax.set_xlabel('Product')
                ax.set_ylabel('Total Count')
                ax.set_title(f"Total Count by Product for {month}")
                plt.xticks(rotation=45)
                st.pyplot(fig)

            else:
                st.warning(f"No data found for the month {month}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
