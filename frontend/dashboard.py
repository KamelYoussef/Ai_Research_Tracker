from fetch_utils import *

st.set_page_config(
    page_title="Dashboard Tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main function to run the app."""
    month = setup_sidebar()

    # Button to fetch and display combined data
    if st.sidebar.button("Fetch Data"):
        if month:
            display_dashboard(month)
        else:
            st.error("Please enter a valid month in the YYYYMM format.")

    if st.sidebar.button("AI Tracking"):
        display_ai_tracking()


# Run the app
if __name__ == "__main__":
    main()
