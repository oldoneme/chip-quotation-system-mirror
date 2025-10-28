#!/usr/bin/env python3
"""
统一审批API端点 - Step 3
按照渐进式开发原则，提供统一的审批操作入口
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ....database import get_db
from ....auth_routes import get_current_user
from ....models import User
from ....services.unified_approval_service import UnifiedApprovalService

# 请求数据模型
class ApprovalRequest(BaseModel):
    comments: Optional[str] = None
    method: Optional[str] = None  # "wecom" | "internal" | null (自动选择)

class RejectRequest(BaseModel):
    reason: str
    comments: Optional[str] = None
    method: Optional[str] = None

# 创建路由器
router = APIRouter()

@router.post("/submit/{quote_id}")
async def submit_approval(
    quote_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一提交审批入口
    自动选择最佳审批方式（企业微信优先，内部审批回退）
    """
    try:
        service = UnifiedApprovalService(db)
        result = service.submit_approval(quote_id, current_user.id)

        return {
            "message": "审批已提交",
            "approval_method": result.approval_method.value,
            "new_status": result.new_status.value,
            "approval_id": result.approval_id,
            "success": result.success
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提交审批失败: {str(e)}"
        )

@router.post("/approve/{quote_id}")
async def approve_quote(
    quote_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一批准入口
    自动选择合适的审批方式进行批准
    """
    try:
        service = UnifiedApprovalService(db)
        result = service.approve(
            quote_id=quote_id,
            approver_id=current_user.id,
            comments=request.comments or "批准"
        )

        return {
            "message": "报价单已批准",
            "approval_method": result.approval_method.value,
            "new_status": result.new_status.value,
            "success": result.success
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批准失败: {str(e)}"
        )

@router.post("/reject/{quote_id}")
async def reject_quote(
    quote_id: str,
    request: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一拒绝入口
    自动选择合适的审批方式进行拒绝
    """
    try:
        service = UnifiedApprovalService(db)
        result = service.reject(
            quote_id=quote_id,
            approver_id=current_user.id,
            reason=request.reason
        )

        return {
            "message": "报价单已拒绝",
            "approval_method": result.approval_method.value,
            "new_status": result.new_status.value,
            "success": result.success
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"拒绝失败: {str(e)}"
        )

@router.get("/status/{quote_id}")
async def get_approval_status(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一审批状态查询
    返回统一格式的审批状态信息
    """
    try:
        # 查询报价单
        from ....models import Quote
        quote = db.query(Quote).filter(Quote.id == quote_id, Quote.is_deleted == False).first()

        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")

        # 返回统一格式的状态信息
        return {
            "quote_id": quote.id,
            "quote_number": quote.quote_number,
            "status": quote.status,
            "approval_status": quote.approval_status,
            "submitted_at": quote.submitted_at,
            "approved_at": quote.approved_at,
            "approved_by": quote.approved_by,
            "rejection_reason": quote.rejection_reason,
            "wecom_approval_id": quote.wecom_approval_id,
            "has_wecom_approval": bool(quote.wecom_approval_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询状态失败: {str(e)}"
        )

@router.get("/history/{quote_id}")
async def get_approval_history(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一审批历史查询
    返回标准化的审批历史记录
    """
    try:
        from ....models import ApprovalRecord

        # 查询审批记录
        records = (
            db.query(ApprovalRecord)
            .filter(ApprovalRecord.quote_id == quote_id)
            .order_by(ApprovalRecord.created_at.desc())
            .all()
        )

        # 格式化返回数据
        history = []
        for record in records:
            history.append({
                "id": record.id,
                "action": record.action,
                "status": record.status,
                "approver_id": record.approver_id,
                "comments": record.comments,
                "processed_at": record.processed_at,
                "created_at": record.created_at
            })

        return {
            "quote_id": quote_id,
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询历史失败: {str(e)}"
        )