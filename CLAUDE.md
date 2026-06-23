# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

学生成绩查询系统 — AI 驱动的成绩查询门户。前端通过 Dify 聊天机器人与 AI 交互，AI 后端连接数据库进行查询。

## 启动命令

```bash
python server.py
```

打开 http://localhost:8080 即可访问。

## 架构

### 后端 (`server.py`)

- **纯静态文件服务器** — 仅使用 Python 标准库 `http.server`
- 零外部依赖，零数据库，只负责托管前端页面
- 数据查询全部由 Dify 工作流中的 AI 处理

### 前端 (`index.html`)

- 纯原生 HTML/CSS/JS，无框架无构建
- 主界面是 **Dify 聊天机器人** 嵌入，用户在对话框中用自然语言查询成绩
- 顶部提供快捷提问按钮（"查一下张明的成绩"等）
- Dify 配置在页面底部 `window.difyChatbotConfig` 中

## 配置

部署前需修改 `index.html` 底部两处：

```js
// 替换为你的 Dify 应用信息
window.difyChatbotConfig = {
  token: 'YOUR_DIFY_TOKEN',
  baseUrl: 'YOUR_DIFY_URL'
}
// 以及对应 script src 地址
```

## 常见任务

- **修改快捷提问**：编辑 `index.html` 中 `.samples` 里的 button 文本
- **更换 Dify 应用**：更新 `token` 和 `baseUrl` 以及 script 的 `src`
- **修改端口**：改 `server.py` 顶部的 `PORT = 8080`
