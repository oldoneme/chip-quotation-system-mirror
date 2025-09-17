#!/usr/bin/env python3
"""
API v2 主路由配置
整合所有v2版本的API端点
"""

from fastapi import APIRouter
from .endpoints.approval_v2 import router as approval_router

# 创建v2 API路由器
api_router = APIRouter(prefix="/v2")

# 注册所有端点
api_router.include_router(approval_router)

# API信息
@api_router.get("/")
async def api_info():
    """V2 API信息"""
    return {
        "name": "芯片报价系统 API v2",
        "version": "2.0.0",
        "description": "统一审批系统 API",
        "features": [
            "统一审批操作接口",
            "智能渠道选择",
            "双向同步支持",
            "完整状态管理",
            "向后兼容保证"
        ],
        "endpoints": {
            "approval": {
                "operate": "POST /v2/approval/{quote_id}/operate",
                "status": "GET /v2/approval/{quote_id}/status",
                "list": "GET /v2/approval/list",
                "approve": "POST /v2/approval/{quote_id}/approve",
                "reject": "POST /v2/approval/{quote_id}/reject",
                "submit": "POST /v2/approval/{quote_id}/submit"
            }
        }
    }