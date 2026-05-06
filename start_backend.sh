#!/bin/bash
echo "🚀 启动芯片报价系统后端服务..."
"$(cd "$(dirname "$0")" && pwd)/scripts/ensure_cloudflare_tunnel.sh" --ensure || { echo "❌ Cloudflare tunnel 未就绪，后端启动中止"; exit 1; }
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
