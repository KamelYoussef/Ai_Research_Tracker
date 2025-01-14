import streamlit as st
import requests
import os
from dotenv import load_dotenv
from data.fetch_utils import validate_token, login

# Load environment variables
load_dotenv()

# Validate FastAPI URL
FASTAPI_URL = os.getenv("FASTAPI_URL")
if not FASTAPI_URL:
    st.error("API Error in the environment variables.")
    st.stop()

st.set_page_config(
    page_title="Sign in",
    layout="centered",
)

# Check if the user is logged in and the token is valid
if st.session_state.get("logged_in") and validate_token():
    st.switch_page("pages/webapp.py")  # Navigate to the main page
else:
    login()  # Show the login page
