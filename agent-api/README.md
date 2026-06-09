# Estevan Cyber Knowledge Agent

FastAPI + LangChain + DeepSeek 的个人网站知识库问答服务。它读取 Hugo `content/` 目录下的 Markdown，检索相关文章片段，再调用 DeepSeek 生成回答。

## 本地运行

```powershell
cd agent-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env.local
```

把 `DEEPSEEK_API_KEY` 写入 `.env.local` 或系统环境变量。不要提交真实密钥。

### 联网搜索（可选）

当本地知识库检索分数低于阈值时，服务会自动调用 Tavily 联网搜索补充结果。

1. 在 [tavily.com](https://tavily.com) 注册并获取 API Key（免费额度每月 1000 次）
2. 将 `TAVILY_API_KEY` 写入 `.env.local` 或环境变量
3. 可通过 `ASK_AGENT_LOCAL_SCORE_THRESHOLD`（默认 `2.0`）调整触发阈值——值越高越容易触发联网搜索

不设置 `TAVILY_API_KEY` 则联网搜索自动禁用，服务仅使用本地知识库。

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek Key"
$env:KNOWLEDGE_CONTENT_DIR="..\content"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## API

### Health

```bash
curl http://127.0.0.1:8000/api/health
```

### Ask

```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hermes Agent 怎么部署？","session_id":"web"}'
```

返回字段：

- `answer`: 生成回答
- `sources`: 引用来源，包含标题、URL、片段和检索分数
- `session_id`: 多轮会话 ID
- `trace_id`: 排错追踪 ID

### Reindex

```bash
curl -X POST http://127.0.0.1:8000/api/reindex
```

## Docker

从仓库根目录构建：

```bash
docker build -f agent-api/Dockerfile -t estevan-knowledge-agent .
docker run --rm -p 8000:8000 \
  -e DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
  -e TAVILY_API_KEY="$TAVILY_API_KEY" \
  -e SITE_BASE_URL="https://blog.estevancyber.net" \
  estevan-knowledge-agent
```

VPS 上建议通过 Nginx/Cloudflare 暴露为 `https://api.estevancyber.net`，Hugo 前端只调用这个 API 域名。
