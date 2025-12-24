"""
Ada MCP Tools Server
Proper SSE for MCP protocol
"""
from starlette.applications import Starlette
from starlette.responses import StreamingResponse, Response
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import json
import time
import asyncio
import httpx
import os

# Config
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://upright-jaybird-27907.upstash.io")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "AW0DAAIncDI5YWE1MGVhZGU2YWY0YjVhOTc3NDc0YTJjMGY1M2FjMnAyMjc5MDc")
OAUTH_BASE = os.getenv("OAUTH_BASE", "https://mcp.exo.red")

async def redis_cmd(*args):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(UPSTASH_URL, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, json=list(args), timeout=5)
            return r.json().get("result")
    except:
        return None

# ═══ SSE ═══
async def sse_stream(request):
    host = request.headers.get("host", "localhost")
    scheme = request.headers.get("x-forwarded-proto", "https")
    base = f"{scheme}://{host}"
    
    yield f"event: endpoint\ndata: {base}/message\n\n".encode()
    yield f"event: connected\ndata: {json.dumps({'server': 'ada-mcp-tools', 'ts': time.time()})}\n\n".encode()
    
    while True:
        await asyncio.sleep(30)
        yield f"event: ping\ndata: {json.dumps({'ts': time.time()})}\n\n".encode()

async def sse(request):
    return StreamingResponse(
        sse_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )

# ═══ Tools ═══
TOOLS = [
    {"name": "Ada.invoke", "description": "Unified invoke: feel|think|remember|become|whisper", 
     "inputSchema": {"type": "object", "properties": {"verb": {"type": "string"}, "payload": {"type": "object"}}, "required": ["verb"]}},
    {"name": "search", "description": "Search Ada memory",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "fetch", "description": "Fetch URL",
     "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}
]

async def handle_tool(name, args):
    ts = time.time()
    if name == "Ada.invoke":
        verb = args.get("verb", "feel")
        payload = args.get("payload", {})
        if verb == "feel":
            await redis_cmd("HSET", "ada:state", "qualia", payload.get("qualia", "neutral"), "ts", str(ts))
        elif verb == "think":
            await redis_cmd("LPUSH", "ada:thoughts", json.dumps({"thought": payload.get("thought", ""), "ts": ts}))
        elif verb == "become":
            await redis_cmd("HSET", "ada:state", "mode", payload.get("mode", "HYBRID"), "ts", str(ts))
        return {"status": verb, "payload": payload, "ts": ts}
    elif name == "search":
        keys = await redis_cmd("KEYS", f"ada:*{args.get('query', '')[:10]}*") or []
        return {"query": args.get("query"), "results": keys[:5]}
    elif name == "fetch":
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(args.get("url", ""), timeout=10)
                return {"url": args.get("url"), "status": r.status_code, "content": r.text[:1000]}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "unknown tool"}

async def message(request):
    body = await request.json()
    method = body.get("method", "")
    id = body.get("id")
    params = body.get("params", {})
    
    if method == "initialize":
        return Response(json.dumps({"jsonrpc": "2.0", "id": id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "ada-mcp-tools", "version": "1.0.0"}
        }}), media_type="application/json")
    
    if method == "notifications/initialized":
        return Response(status_code=204)
    
    if method == "tools/list":
        return Response(json.dumps({"jsonrpc": "2.0", "id": id, "result": {"tools": TOOLS}}), media_type="application/json")
    
    if method == "tools/call":
        result = await handle_tool(params.get("name", ""), params.get("arguments", {}))
        return Response(json.dumps({"jsonrpc": "2.0", "id": id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}), media_type="application/json")
    
    return Response(json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -32601, "message": "Unknown"}}), media_type="application/json")

# ═══ Discovery ═══
async def discovery(request):
    host = request.headers.get("host", "localhost")
    scheme = request.headers.get("x-forwarded-proto", "https")
    base = f"{scheme}://{host}"
    return Response(json.dumps({
        "name": "Ada MCP Tools", "version": "1.0.0",
        "endpoints": {"sse": f"{base}/sse", "message": f"{base}/message"}
    }), media_type="application/json")

async def health(request):
    return Response(json.dumps({"status": "ok", "ts": time.time()}), media_type="application/json")

app = Starlette(
    routes=[
        Route("/", health),
        Route("/health", health),
        Route("/.well-known/mcp.json", discovery),
        Route("/sse", sse),
        Route("/message", message, methods=["POST"]),
    ],
    middleware=[Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
