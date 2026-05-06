#!/bin/bash
echo "🚀 启动芯片报价系统前端应用..."
"$(cd "$(dirname "$0")" && pwd)/scripts/ensure_cloudflare_tunnel.sh" --ensure || { echo "❌ Cloudflare tunnel 未就绪，前端启动中止"; exit 1; }
cd frontend/chip-quotation-frontend
npm start
