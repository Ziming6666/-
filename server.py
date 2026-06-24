#!/usr/bin/env python3
"""
学生成绩查询系统 - FastAPI 服务器
提供静态文件服务 + Dify 流式 API 代理
"""

import json
import os
import httpx
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

PORT = int(os.getenv("PORT", "8080"))
BASE_DIR = Path(__file__).parent

# Dify 配置 — 优先从环境变量读取（方便云部署）
DIFY_HOST = os.getenv("DIFY_HOST", "localhost")
DIFY_PORT = os.getenv("DIFY_PORT", "80")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "app-BxWcOSgIOr23D54hVFOiMCGy")
DIFY_BASE = os.getenv("DIFY_BASE_URL", f"http://{DIFY_HOST}:{DIFY_PORT}")

app = FastAPI(title="学生成绩查询系统")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Dify 流式代理 API
# ============================================================

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    query = body.get("query", "").strip()
    conversation_id = body.get("conversation_id", "")

    if not query:
        return JSONResponse({"error": "请输入查询内容"}, status_code=400)

    payload = {
        "inputs": {},
        "query": query,
        "user": "web-user",
        "response_mode": "streaming",
        "conversation_id": conversation_id,
    }

    async def event_stream():
        answer_parts = []
        new_conv_id = conversation_id

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{DIFY_BASE}/v1/chat-messages",
                    json=payload,
                    headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
                ) as resp:
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue

                        try:
                            evt = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue

                        et = evt.get("event", "")

                        if et == "message":
                            ans = evt.get("answer", "")
                            if ans:
                                answer_parts.append(ans)
                                full = "".join(answer_parts)
                                yield f"data: {json.dumps({'event': 'message', 'answer': full}, ensure_ascii=False)}\n\n"

                        elif et == "message_end":
                            if evt.get("conversation_id"):
                                new_conv_id = evt["conversation_id"]
                            yield f"data: {json.dumps({'event': 'message_end', 'conversation_id': new_conv_id}, ensure_ascii=False)}\n\n"

                        elif et == "workflow_finished":
                            outputs = evt.get("data", {}).get("outputs", {})
                            if outputs and outputs.get("answer"):
                                yield f"data: {json.dumps({'event': 'message', 'answer': outputs['answer'], '_final': True}, ensure_ascii=False)}\n\n"

                        elif et == "error":
                            yield f"data: {json.dumps({'event': 'error', 'message': evt.get('message', '未知错误')}, ensure_ascii=False)}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*"},
    )


# ============================================================
# 静态文件服务（API 路由之后注册，避免覆盖）
# ============================================================

@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "index.html"))


@app.get("/{filename:path}")
async def static_files(filename: str):
    file_path = BASE_DIR / filename
    if file_path.is_file():
        return FileResponse(str(file_path))
    # 如果是目录/子路径，尝试 index.html
    index_path = file_path / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path))
    return JSONResponse({"error": "Not Found"}, status_code=404)


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 48)
    print("  学生成绩查询系统 — FastAPI")
    print("=" * 48)
    print(f"\n  地址: http://localhost:{PORT}")
    print(f"\n  ngrok 穿透: ngrok http {PORT}")
    print(f"\n按 Ctrl+C 停止\n")

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
