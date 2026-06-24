# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

学生成绩查询系统 — AI 驱动的成绩查询门户。FastAPI 后端 + Dify AI 工作流。

## 启动命令

```bash
# 安装依赖（首次）
pip install fastapi uvicorn httpx

# 启动服务器
python server.py

# 用 ngrok 分享给其他人
ngrok http 8080
```

## 架构

```
用户 ←→ 浏览器 (index.html)
         ↓ POST /api/chat (SSE 流式)
     FastAPI (server.py)
         ↓ POST /v1/chat-messages (streaming)
     Dify API (localhost:80)
         ↓ 执行工作流
     数据库 (SQL/MySQL)
```

### 文件结构

| 文件 | 说明 |
|---|---|
| `server.py` | FastAPI 服务器：静态文件服务 + Dify 流式代理 |
| `index.html` | 聊天界面：流式显示文字 + ECharts 图表 |
| `wechat_channel.py` | 企业微信通道（可选） |
| `学生数据库系统查询助手.yml` | Dify 工作流 DSL 配置 |

### API

- `POST /api/chat` — Dify 流式代理，返回 SSE
  - 请求: `{"query": "...", "conversation_id": "..."}`
  - 响应: SSE 流，事件类型 `message` / `message_end` / `error`

## 配置

在 `server.py` 中修改：

```python
DIFY_HOST = "localhost"    # Dify 地址
DIFY_PORT = 80              # Dify 端口
DIFY_API_KEY = "app-xxx"   # API 密钥
```
