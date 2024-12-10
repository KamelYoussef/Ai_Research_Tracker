import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from fetch_utils import *

st.title("AI Tracking")
st.sidebar.header("AI Tracking Settings")

if st.sidebar.button("Run AI Tracking"):
    display_ai_tracking()
