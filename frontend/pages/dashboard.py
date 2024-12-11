import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data.fetch_utils import *

st.title("Dashboard")
st.sidebar.header("Dashboard Settings")

month = setup_sidebar()
if st.sidebar.button("Fetch Data"):
    if month:
        display_dashboard(month)
    else:
        st.error("Please enter a valid month in the YYYYMM format.")
