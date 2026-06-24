# 学生成绩查询系统 🎓

AI 驱动的学生成绩查询门户。FastAPI 后端 + Dify AI 工作流，支持流式 SSE 响应和 ECharts 图表渲染。

## 在线体验

[https://sunny-playfulness-production-8591.up.railway.app](https://sunny-playfulness-production-8591.up.railway.app)

## 启动方式

```bash
# 安装依赖
pip install fastapi uvicorn httpx

# 启动服务器（本地开发）
python server.py
# 访问 http://localhost:8080
```

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | 原生 HTML/CSS/JS，ECharts 图表 |
| 后端 | FastAPI + Uvicorn |
| AI 引擎 | Dify 工作流（通义千问 + 数据库插件） |
| 通信 | SSE 流式代理 |
| 部署 | Railway（云端）+ ngrok（本地 Dify 隧道） |

## 架构

```
用户 → 浏览器 → Railway (FastAPI 云端)
                   ↓ POST /api/chat (SSE 流式)
               server.py (代理转发)
                   ↓ POST /v1/chat-messages (streaming)
               ngrok 隧道 → 本地 Dify Docker
                   ↓ 执行工作流→生成SQL→查询数据库
                   ↓ SSE 流式返回
               浏览器实时渲染（文字 + ECharts 图表）
```

## 项目文件

```
学生数据库成绩查询/
├── server.py                  # FastAPI 服务器（静态文件 + API代理）
├── index.html                 # 聊天界面（流式文字 + ECharts 图表）
├── wechat_channel.py          # 企业微信通道（可选）
├── main.py                    # Railway 部署入口
├── requirements.txt           # Python 依赖
├── 学生数据库系统查询助手.yml  # Dify 工作流 DSL 配置
├── CLAUDE.md                  # AI 开发助手指南
├── README.md                  # 本文件
└── .gitignore
```

## 部署到云

本项目部署在 Railway，通过 ngrok 隧道连接本地 Dify：

```bash
# 本地启动 ngrok，暴露 Dify API
.\ngrok.exe http 80

# Railway 设置环境变量
DIFY_BASE_URL = https://你的ngrok地址.ngrok-free.dev
```

## 配置

通过环境变量配置（支持 `.env` 或 Railway Dashboard）：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DIFY_BASE_URL` | `http://localhost:80` | Dify API 地址 |
| `DIFY_API_KEY` | `app-BxWcOSgIOr23D54hVFOiMCGy` | Dify API 密钥 |
| `PORT` | `8080` | 服务端口 |
