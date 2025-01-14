import streamlit as st
from data.fetch_utils import validate_token, login

st.set_page_config(
    page_title="Sign in",
    layout="centered",
)

# Check if the user is logged in and the token is valid
if st.session_state.get("logged_in") and validate_token():
    st.switch_page("pages/webapp.py")  # Navigate to the main page
else:
    login()  # Show the login page
