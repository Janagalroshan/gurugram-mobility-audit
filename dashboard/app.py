"""Entry point — redirects to the Executive Summary page."""
import streamlit as st

st.set_page_config(page_title="Gurugram Mobility Audit", layout="wide")

try:
    st.switch_page("pages/0_Executive_Summary.py")
except Exception:
    st.title("Gurugram Urban Mobility Audit Dashboard")
    st.write("Use the sidebar to navigate to Executive Summary and other pages.")
