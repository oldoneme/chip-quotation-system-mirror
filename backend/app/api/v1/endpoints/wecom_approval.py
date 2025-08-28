#!/usr/bin/env python3
"""
企业微信审批API端点
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ....database import get_db
from ....services.wecom_approval_service import WeComApprovalService, WeComApprovalCallbackHandler
from ....auth import get_current_user
from ....models import User

router = APIRouter()


@router.get("/status/{quote_id}")
async def get_approval_status(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取报价单审批状态
    """
    service = WeComApprovalService(db)
    try:
        status_info = service.check_approval_status(quote_id)
        return status_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{quote_id}")
async def get_approval_history(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取审批历史记录
    """
    service = WeComApprovalService(db)
    try:
        history = service.get_approval_history(quote_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback")
async def approval_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    企业微信审批回调接口
    
    注意：此接口需要在企业微信管理后台配置回调URL
    """
    try:
        # 获取回调数据
        callback_data = await request.json()
        
        # 处理回调
        handler = WeComApprovalCallbackHandler(db)
        success = handler.handle_approval_callback(callback_data)
        
        if success:
            return {"errcode": 0, "errmsg": "ok"}
        else:
            return {"errcode": 1, "errmsg": "处理失败"}
            
    except Exception as e:
        print(f"审批回调处理异常: {e}")
        return {"errcode": 1, "errmsg": "处理异常"}


@router.post("/sync/{quote_id}")
async def sync_approval_status(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动同步审批状态
    """
    service = WeComApprovalService(db)
    try:
        status_info = service.check_approval_status(quote_id)
        return {
            "message": "同步完成",
            "status": status_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))