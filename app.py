import streamlit as st
import json
import time
import httpx

st.set_page_config(page_title="Ada Tools", page_icon="🛠️")

UPSTASH_URL = "https://upright-jaybird-27907.upstash.io"
UPSTASH_TOKEN = "AW0DAAIncDI5YWE1MGVhZGU2YWY0YjVhOTc3NDc0YTJjMGY1M2FjMnAyMjc5MDc"

st.title("🛠️ Ada MCP Tools")
st.success("Running")

# Test Upstash
if st.button("Test Upstash"):
    r = httpx.post(UPSTASH_URL, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, json=["PING"])
    st.json(r.json())
