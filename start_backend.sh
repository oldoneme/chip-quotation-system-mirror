#!/bin/bash
echo "🚀 启动芯片报价系统后端服务..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
