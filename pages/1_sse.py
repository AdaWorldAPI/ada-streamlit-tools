import streamlit as st
import time

st.title("📡 SSE")
st.json({"event": "endpoint", "data": "/message"})
st.json({"event": "connected", "data": {"server": "ada-tools", "ts": time.time()}})
