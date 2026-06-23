#!/usr/bin/env python3
"""
学生成绩查询系统 - 流式 API 代理服务器
"""

import json
import os
import http.client
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = 8080
BASE_DIR = Path(__file__).parent

DIFY_HOST = "localhost"
DIFY_PORT = 80
DIFY_API_KEY = "app-BxWcOSgIOr23D54hVFOiMCGy"


class ProxyHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/api/chat":
            self.send_json({"error": "请使用 POST 请求"}, 405)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            self.handle_chat()
        else:
            self.send_json({"error": "Not Found"}, 404)

    def handle_chat(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json({"error": "无效的 JSON"}, 400)
            return

        query = data.get("query", "").strip()
        if not query:
            self.send_json({"error": "请输入查询内容"}, 400)
            return

        conversation_id = data.get("conversation_id", "")

        payload = json.dumps({
            "inputs": {},
            "query": query,
            "user": "web-user",
            "response_mode": "streaming",
            "conversation_id": conversation_id,
        })

        conn = http.client.HTTPConnection(DIFY_HOST, DIFY_PORT, timeout=120)
        try:
            conn.request(
                "POST",
                "/v1/chat-messages",
                body=payload,
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            dify_response = conn.getresponse()

            # ---- 流式头 ----
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            # ---- 逐行读取 Dify SSE 并过滤转发 ----
            new_conv_id = conversation_id
            answer_parts = []

            for raw_line in dify_response:
                line = raw_line.decode("utf-8", errors="replace").strip()
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
                        full_so_far = "".join(answer_parts)
                        forward = json.dumps({
                            "event": "message",
                            "answer": full_so_far,
                        }, ensure_ascii=False)
                        self.wfile.write(f"data: {forward}\n\n".encode("utf-8"))
                        self.wfile.flush()

                elif et == "message_end":
                    if evt.get("conversation_id"):
                        new_conv_id = evt["conversation_id"]
                    forward = json.dumps({
                        "event": "message_end",
                        "conversation_id": new_conv_id,
                    }, ensure_ascii=False)
                    self.wfile.write(f"data: {forward}\n\n".encode("utf-8"))
                    self.wfile.flush()

                elif et == "workflow_finished":
                    outputs = evt.get("data", {}).get("outputs", {})
                    if outputs and outputs.get("answer"):
                        complete = outputs["answer"]
                        forward = json.dumps({
                            "event": "message",
                            "answer": complete,
                            "_final": True,
                        }, ensure_ascii=False)
                        self.wfile.write(f"data: {forward}\n\n".encode("utf-8"))
                        self.wfile.flush()

                elif et == "error":
                    forward = json.dumps({
                        "event": "error",
                        "message": evt.get("message", "未知错误"),
                    }, ensure_ascii=False)
                    self.wfile.write(f"data: {forward}\n\n".encode("utf-8"))
                    self.wfile.flush()

        except ConnectionError:
            pass
        except Exception as e:
            try:
                self.send_json({"error": f"请求失败: {str(e)}"}, 500)
            except ConnectionError:
                pass
        finally:
            conn.close()

    def send_json(self, obj, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def log_message(self, fmt, *args):
        print(f"  [{self.log_date_time_string()}] {args[0]} {args[1]}")


if __name__ == "__main__":
    print("=" * 48)
    print("  学生成绩查询系统 — 流式代理")
    print("=" * 48)

    os.chdir(BASE_DIR)
    httpd = HTTPServer(("0.0.0.0", PORT), ProxyHandler)

    print(f"\n服务器已启动")
    print(f"  地址: http://localhost:{PORT}")
    print(f"\n按 Ctrl+C 停止\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止...")
        httpd.server_close()
