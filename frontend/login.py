import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the FastAPI server URL
FASTAPI_URL = os.getenv("FASTAPI_URL")

st.set_page_config(
    page_title="Sign in",
    layout="centered",
)

def login():

    st.header("Sign in to AI Tracker")
    with st.form("login_form", clear_on_submit=True):
        # Username input field
        username = st.text_input("Username")

        # Password input field (hidden)
        password = st.text_input("Password", type="password")

        # Submit button with custom style
        login_button = st.form_submit_button("Login", use_container_width=True)

        if login_button:
            with st.spinner("Logging in..."):
                # Send login request to FastAPI
                response = requests.post(
                    f"{FASTAPI_URL}/login",
                    json={"username": username, "password": password},
                )

                if response.status_code == 200:
                    # Successful login, get the token
                    token = response.json()["access_token"]
                    st.session_state.token = token  # Store token in session
                    st.success("Login successful!")

                    # Set the flag indicating the user is logged in
                    st.session_state.logged_in = True

                    # Rerun the app to redirect to the main page
                    st.rerun()
                else:
                    # Handle failed login
                    error_message = response.json().get('detail', 'Unknown error')
                    st.error(f"Login failed: {error_message}")


# Check if the user is logged in
if 'logged_in' in st.session_state and st.session_state.logged_in:
    st.switch_page("pages/webapp.py")  # Show the main page after login

else:
    login()  # --client.showSidebarNavigation=False
