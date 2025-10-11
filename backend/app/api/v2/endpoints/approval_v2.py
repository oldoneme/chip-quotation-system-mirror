#!/usr/bin/env python3
"""
统一审批API v2 - Step 3实施
整合现有分散的审批端点，提供统一的API接口
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....database import get_db
from ....auth import get_current_user
from ....models import User, Quote, ApprovalRecord
from ....services.approval_engine import (
    UnifiedApprovalEngine,
    ApprovalOperation,
    ApprovalAction,
    OperationChannel,
    ApprovalStatus
)

# === API 数据模型 ===

class ApprovalOperationRequest(BaseModel):
    """统一审批操作请求"""
    action: str = Field(..., description="审批动作: approve, reject, withdraw, submit")
    comments: Optional[str] = Field(None, description="审批意见")
    reason: Optional[str] = Field(None, description="拒绝原因 (仅reject时需要)")
    channel: Optional[str] = Field("auto", description="操作渠道: auto, internal, wecom")
    delegate_to: Optional[int] = Field(None, description="委托给用户ID (仅delegate时需要)")

class ApprovalStatusResponse(BaseModel):
    """审批状态响应"""
    quote_id: int
    quote_number: str
    current_status: str
    approval_status: str
    can_approve: bool
    can_reject: bool
    can_withdraw: bool
    approval_history: List[Dict[str, Any]]
    wecom_approval_id: Optional[str] = None
    last_updated: datetime

class ApprovalOperationResponse(BaseModel):
    """审批操作响应"""
    success: bool
    message: str
    new_status: str
    operation_id: Optional[str] = None
    sync_required: bool = False
    errors: Optional[List[str]] = None

class ApprovalListResponse(BaseModel):
    """审批列表响应"""
    total: int
    items: List[ApprovalStatusResponse]
    page: int
    page_size: int

# === 路由器初始化 ===
router = APIRouter(prefix="/approval", tags=["审批管理 v2"])

# === 核心审批操作端点 ===

@router.post("/{quote_id}/operate", response_model=ApprovalOperationResponse)
async def execute_approval_operation(
    quote_id: int,
    request: ApprovalOperationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    统一审批操作入口
    支持所有审批动作：提交、批准、拒绝、撤回、委托
    """
    try:
        # 初始化统一审批引擎
        approval_engine = UnifiedApprovalEngine(db)

        # 映射操作渠道
        channel_mapping = {
            "auto": OperationChannel.INTERNAL,  # 默认为内部操作，触发企业微信通知
            "internal": OperationChannel.INTERNAL,
            "wecom": OperationChannel.WECOM,
            "api": OperationChannel.INTERNAL  # API调用也视为内部操作
        }

        operation_channel = channel_mapping.get(request.channel, OperationChannel.INTERNAL)

        # 映射审批动作
        action_mapping = {
            "submit": ApprovalAction.SUBMIT,
            "approve": ApprovalAction.APPROVE,
            "reject": ApprovalAction.REJECT,
            "withdraw": ApprovalAction.WITHDRAW,
            "delegate": ApprovalAction.DELEGATE
        }

        if request.action not in action_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的操作类型: {request.action}"
            )

        approval_action = action_mapping[request.action]

        # 构建审批操作对象
        operation = ApprovalOperation(
            action=approval_action,
            quote_id=quote_id,
            operator_id=current_user.id,
            channel=operation_channel,
            comments=request.comments,
            reason=request.reason,
            delegate_to=request.delegate_to
        )

        # 执行审批操作
        result = approval_engine.execute_operation(operation)

        if result.success:
            return ApprovalOperationResponse(
                success=True,
                message=result.message,
                new_status=result.new_status.value,
                operation_id=result.operation_id,
                sync_required=result.sync_required
            )
        else:
            return ApprovalOperationResponse(
                success=False,
                message=result.message,
                new_status=result.new_status.value,
                errors=[result.message]
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"操作执行失败: {str(e)}"
        )

# === 状态查询端点 ===

@router.get("/{quote_id}/status", response_model=ApprovalStatusResponse)
async def get_approval_status(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取统一审批状态
    返回完整的审批信息和可执行操作
    """
    try:
        # 查询报价单
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报价单不存在: {quote_id}"
            )

        # 查询审批历史
        approval_history = db.query(ApprovalRecord).filter(
            ApprovalRecord.quote_id == quote_id
        ).order_by(ApprovalRecord.created_at.desc()).all()

        # 构建审批历史数据
        history_data = []
        for record in approval_history:
            # 获取审批人信息
            approver_name = "系统"
            if record.approver_id:
                approver = db.query(User).filter(User.id == record.approver_id).first()
                if approver:
                    approver_name = approver.name or approver.userid or f"用户{approver.id}"

            history_data.append({
                "id": record.id,
                "action": record.action,
                "status": record.status,
                "approver_name": approver_name,
                "operator": approver_name,
                "comments": record.comments,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "processed_at": record.processed_at.isoformat() if record.processed_at else None,
                "channel": "wecom" if record.wecom_sp_no else "internal"
            })

        # 初始化审批引擎检查权限
        approval_engine = UnifiedApprovalEngine(db)
        current_status = ApprovalStatus(quote.status)

        # 检查用户可执行的操作
        can_approve = approval_engine.state_machine.validate_transition(
            current_status, ApprovalStatus.APPROVED
        )
        can_reject = approval_engine.state_machine.validate_transition(
            current_status, ApprovalStatus.REJECTED
        )
        can_withdraw = approval_engine.state_machine.validate_transition(
            current_status, ApprovalStatus.WITHDRAWN
        )

        return ApprovalStatusResponse(
            quote_id=quote.id,
            quote_number=quote.quote_number,
            current_status=quote.status,
            approval_status=quote.approval_status or quote.status,
            can_approve=can_approve,
            can_reject=can_reject,
            can_withdraw=can_withdraw,
            approval_history=history_data,
            wecom_approval_id=quote.wecom_approval_id,
            last_updated=quote.updated_at or quote.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"状态查询失败: {str(e)}"
        )

# === 批量查询端点 ===

@router.get("/list", response_model=ApprovalListResponse)
async def list_approvals(
    status_filter: Optional[str] = Query(None, description="状态过滤: pending, approved, rejected"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="页大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取审批列表
    支持状态过滤和分页
    """
    try:
        # 构建查询
        query = db.query(Quote)

        # 状态过滤
        if status_filter:
            query = query.filter(Quote.status == status_filter)

        # 计算总数
        total = query.count()

        # 分页查询
        offset = (page - 1) * page_size
        quotes = query.offset(offset).limit(page_size).all()

        # 构建响应数据
        items = []
        for quote in quotes:
            # 简化的审批历史（只取最近5条）
            recent_history = db.query(ApprovalRecord).filter(
                ApprovalRecord.quote_id == quote.id
            ).order_by(ApprovalRecord.created_at.desc()).limit(5).all()

            history_data = [{
                "action": record.action,
                "status": record.status,
                "created_at": record.created_at,
                "comments": record.comments
            } for record in recent_history]

            items.append(ApprovalStatusResponse(
                quote_id=quote.id,
                quote_number=quote.quote_number,
                current_status=quote.status,
                approval_status=quote.approval_status or quote.status,
                can_approve=quote.status == "pending",
                can_reject=quote.status == "pending",
                can_withdraw=quote.status == "pending",
                approval_history=history_data,
                wecom_approval_id=quote.wecom_approval_id,
                last_updated=quote.updated_at or quote.created_at
            ))

        return ApprovalListResponse(
            total=total,
            items=items,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列表查询失败: {str(e)}"
        )

# === 便捷操作端点 (向后兼容) ===

@router.post("/{quote_id}/approve", response_model=ApprovalOperationResponse)
async def approve_quote(
    quote_id: int,
    comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """便捷批准端点 (向后兼容V1)"""
    request = ApprovalOperationRequest(
        action="approve",
        comments=comments,
        channel="auto"
    )
    return await execute_approval_operation(quote_id, request, db, current_user)

@router.post("/{quote_id}/reject", response_model=ApprovalOperationResponse)
async def reject_quote(
    quote_id: int,
    reason: str,
    comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """便捷拒绝端点 (向后兼容V1)"""
    request = ApprovalOperationRequest(
        action="reject",
        reason=reason,
        comments=comments,
        channel="auto"
    )
    return await execute_approval_operation(quote_id, request, db, current_user)

@router.post("/{quote_id}/submit", response_model=ApprovalOperationResponse)
async def submit_quote(
    quote_id: int,
    comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """便捷提交端点 (向后兼容V1)"""
    request = ApprovalOperationRequest(
        action="submit",
        comments=comments,
        channel="auto"
    )
    return await execute_approval_operation(quote_id, request, db, current_user)

# === 健康检查端点 ===

@router.get("/health")
async def health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "version": "v2",
        "timestamp": datetime.now(),
        "features": [
            "unified_operations",
            "status_queries",
            "batch_listing",
            "backward_compatibility"
        ]
    }