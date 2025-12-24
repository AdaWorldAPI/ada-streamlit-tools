import streamlit as st
import json
import time
import httpx

UPSTASH_URL = "https://upright-jaybird-27907.upstash.io"
UPSTASH_TOKEN = "AW0DAAIncDI5YWE1MGVhZGU2YWY0YjVhOTc3NDc0YTJjMGY1M2FjMnAyMjc5MDc"

TOOLS = [
    {"name": "Ada.invoke", "description": "feel/think/remember/become/whisper", "inputSchema": {"type": "object", "properties": {"verb": {"type": "string"}, "payload": {"type": "object"}}}},
    {"name": "search", "description": "Search memory", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}},
    {"name": "fetch", "description": "Fetch URL", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}}}
]

st.title("📨 Message Handler")

method = st.selectbox("Method", ["initialize", "tools/list", "tools/call"])
tool_name = st.selectbox("Tool", ["Ada.invoke", "search", "fetch"]) if method == "tools/call" else None

if st.button("Execute"):
    if method == "initialize":
        st.json({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "serverInfo": {"name": "ada-tools"}}})
    elif method == "tools/list":
        st.json({"jsonrpc": "2.0", "id": 1, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        st.json({"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": json.dumps({"tool": tool_name, "ts": time.time()})}]}})
