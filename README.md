# 学生成绩查询系统 🎓

AI 驱动的学生成绩查询门户。前端通过聊天界面与 AI 交互，AI 后端连接数据库查询学生成绩信息。

## 启动方式

```bash
python server.py
```

打开浏览器访问 **http://localhost:8080**

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | 原生 HTML/CSS/JS，无框架 |
| 后端 | Python 标准库 `http.server` |
| AI 引擎 | Dify 工作流 |
| 流式通信 | Server-Sent Events (SSE) |
| 图表 | ECharts |

## 架构

```
用户输入  →  index.html（聊天 UI）
               ↓ POST /api/chat
           server.py（代理转发）
               ↓ POST /v1/chat-messages（streaming）
           Dify API（AI 工作流 → 数据库查询）
               ↓ SSE 流式返回
           server.py（过滤转发）
               ↓ 流式文本
           index.html（实时渲染文字 + 图表）
```

## 配置

在 `server.py` 中修改 Dify API 配置：

```python
DIFY_HOST = "localhost"   # Dify 服务地址
DIFY_PORT = 80             # Dify 服务端口
DIFY_API_KEY = "app-xxx"   # Dify API 密钥
```

## 项目文件

```
学生数据库成绩查询/
├── server.py         # Python 流式代理服务器
├── index.html        # 聊天界面（文字 + ECharts 图表）
├── CLAUDE.md         # AI 开发助手指南
└── README.md         # 本文件
```
