# Knowledge Agent VPS Deployment

This checklist keeps the Hugo site static and deploys the Q&A agent as a separate API service.

## Target Layout

```text
blog.estevancyber.net  -> Hugo static site
api.estevancyber.net   -> FastAPI knowledge agent
```

## Environment

Set these on the VPS. Do not commit real secrets.

```bash
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
SITE_BASE_URL=https://blog.estevancyber.net
ASK_AGENT_CORS_ORIGINS=https://blog.estevancyber.net,https://estevancyber.net
```

## Build

From the repository root:

```bash
docker build -f agent-api/Dockerfile -t estevan-knowledge-agent .
```

## Run

```bash
docker run -d --name estevan-knowledge-agent \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -e DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
  -e DEEPSEEK_MODEL="$DEEPSEEK_MODEL" \
  -e DEEPSEEK_BASE_URL="$DEEPSEEK_BASE_URL" \
  -e SITE_BASE_URL="$SITE_BASE_URL" \
  -e ASK_AGENT_CORS_ORIGINS="$ASK_AGENT_CORS_ORIGINS" \
  estevan-knowledge-agent
```

## Nginx

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name api.estevancyber.net;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name api.estevancyber.net;

    ssl_certificate /etc/nginx/ssl/estevancyber/origin.pem;
    ssl_certificate_key /etc/nginx/ssl/estevancyber/origin.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Verify

```bash
curl https://api.estevancyber.net/api/health
curl -X POST https://api.estevancyber.net/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hermes Agent 怎么部署？","session_id":"smoke"}'
```

Then open:

```text
https://blog.estevancyber.net/ask/
```

Ask a question and confirm the response includes sources.
