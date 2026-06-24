#!/usr/bin/env python3
"""
企业微信通道 - FastAPI 版
在微信中向 AI 发送消息并接收回复

使用方式：
1. 注册企业微信 → 创建自建应用 → 配置接收消息 URL
2. 在本文件顶部填写你的企业微信应用信息
3. 启动：python wechat_channel.py
4. ngrok 穿透：ngrok http 9000
5. 企业微信 URL 配置为：https://xxx.ngrok.io/
"""

import json
import hashlib
import time
import xml.etree.ElementTree as ET
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse

# ============================================================
# 配置 — 替换为你的企业微信应用信息
# ============================================================
WX_TOKEN = "your_wx_token"           # 应用管理 → 接收消息 → Token
WX_CORP_ID = "your_corp_id"          # 我的企业 → CorpID
WX_AGENT_SECRET = "your_secret"      # 应用管理 → Secret
WX_AGENT_ID = "1000002"              # 应用管理 → AgentId

# Dify 配置（与 server.py 共用）
DIFY_API_KEY = "app-BxWcOSgIOr23D54hVFOiMCGy"
DIFY_BASE = "http://localhost:80"

PORT = 9000

app = FastAPI(title="学生成绩查询 - 微信通道")


# ============================================================
# 微信消息处理
# ============================================================

def verify_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """验证微信消息签名。"""
    arr = sorted([WX_TOKEN, timestamp, nonce])
    return hashlib.sha1("".join(arr).encode()).hexdigest() == signature


def parse_xml(xml_str: str) -> dict:
    """解析微信 XML 消息。"""
    root = ET.fromstring(xml_str)
    return {
        "msg_type": (root.find("MsgType") or ET.Element("x")).text or "",
        "content": (root.find("Content") or ET.Element("x")).text or "",
        "from_user": (root.find("FromUserName") or ET.Element("x")).text or "",
        "msg_id": (root.find("MsgId") or ET.Element("x")).text or "",
    }


def build_text_reply(to_user: str, from_user: str, content: str) -> str:
    """构造微信文本回复 XML。"""
    timestamp = str(int(time.time()))
    return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""


def simplify_answer(answer: str, max_len: int = 600) -> str:
    """简化 Dify 回答：去掉 echarts 代码块和 SQL，截断过长内容。"""
    # 去掉 echarts 代码块
    if "```echarts" in answer:
        parts = answer.split("```echarts")
        answer = parts[0]
        for part in parts[1:]:
            if "```" in part:
                answer += part.split("```", 1)[1]

    # 去掉 --- 分隔线后的内容
    if "---------------------------" in answer:
        answer = answer.split("---------------------------")[0]

    # 去掉 sql 字样
    answer = answer.replace("sql语句生成中", "").replace("sql语句生成完毕", "")

    answer = answer.strip()
    if len(answer) > max_len:
        answer = answer[: max_len - 3] + "..."
    return answer


async def query_dify(query: str, conversation_id: str = "") -> tuple[str, str]:
    """调 Dify API 获取回答（blocking 模式）。"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{DIFY_BASE}/v1/chat-messages",
                json={
                    "inputs": {},
                    "query": query,
                    "user": "wechat-user",
                    "response_mode": "blocking",
                    "conversation_id": conversation_id,
                },
                headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
            )
            result = resp.json()
            answer = result.get("answer", "抱歉，我没有理解你的问题")
            new_conv_id = result.get("conversation_id", conversation_id)
            answer = simplify_answer(answer)
            return answer, new_conv_id
        except Exception as e:
            return f"查询出错: {str(e)}", conversation_id


# ============================================================
# 路由
# ============================================================

@app.get("/")
async def verify_url(
    msg_signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    echostr: str = "",
):
    """企业微信验证 URL（GET 请求）。"""
    sig = msg_signature or ""
    if verify_signature(sig, timestamp, nonce):
        return PlainTextResponse(echostr)
    return PlainTextResponse("forbidden", status_code=403)


@app.post("/")
async def receive_message(request: Request):
    """接收微信推送的消息（POST 请求）。"""
    # 验证签名
    params = dict(request.query_params)
    sig = params.get("msg_signature", params.get("signature", ""))
    timestamp = params.get("timestamp", "")
    nonce = params.get("nonce", "")

    if not verify_signature(sig, timestamp, nonce):
        return PlainTextResponse("forbidden", status_code=403)

    # 解析 XML 消息
    body = await request.body()
    try:
        msg = parse_xml(body.decode("utf-8"))
    except Exception:
        return PlainTextResponse("success")

    # 只处理文本消息
    if msg["msg_type"] != "text" or not msg["content"]:
        return PlainTextResponse("success")

    print(f"  微信消息: {msg['from_user']} → {msg['content']}")

    # 调 Dify
    answer, _ = await query_dify(msg["content"])

    reply_xml = build_text_reply(msg["from_user"], msg["from_user"], answer)
    return PlainTextResponse(reply_xml, media_type="text/xml; charset=utf-8")


@app.get("/status")
async def status():
    return {"status": "ok", "channel": "wechat", "port": PORT}


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 48)
    print("  微信通道 — FastAPI")
    print("=" * 48)
    print(f"\n  端口: {PORT}")
    print(f"\n  企业微信 URL 配置为:")
    print(f"  http://<公网IP>:{PORT}/")
    print(f"\n  ngrok 穿透:")
    print(f"  ngrok http {PORT}")
    print(f"\n  注意: 如果与 server.py 同时运行,")
    print(f"  需分别穿透两个端口或用 nginx 合并\n")

    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
