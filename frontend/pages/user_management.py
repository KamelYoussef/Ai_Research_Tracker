import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the FastAPI server URL
API_BASE_URL = os.getenv("FASTAPI_URL")

# Admin token (this should be securely stored, e.g., in a secrets manager)
ADMIN_TOKEN = st.session_state.token

# Headers for API requests
HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

st.title("User Management")

# Tabs for adding and deleting users
tab1, tab2 = st.tabs(["Add User", "Delete User"])

# Add User Tab
with tab1:
    st.header("Add User")
    username = st.text_input("Username", key="add_username")
    password = st.text_input("Password", type="password", key="add_password")
    role = st.selectbox("Role", options=["user", "admin"], key="add_role")

    if st.button("Add User"):
        if username and password:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/add_user",
                    headers=HEADERS,
                    json={"username": username, "password": password, "role": role},
                )
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(response.json().get("detail", "An error occurred"))
            except requests.RequestException as e:
                st.error(f"Request failed: {e}")
        else:
            st.warning("Please fill in all fields.")

# Delete User Tab
with tab2:
    st.header("Delete User")
    username_to_delete = st.text_input("Username", key="delete_username")

    if st.button("Delete User"):
        if username_to_delete:
            try:
                response = requests.delete(
                    f"{API_BASE_URL}/delete_user",
                    headers=HEADERS,
                    params={"username": username_to_delete},
                )
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(response.json().get("detail", "An error occurred"))
            except requests.RequestException as e:
                st.error(f"Request failed: {e}")
        else:
            st.warning("Please enter a username to delete.")
