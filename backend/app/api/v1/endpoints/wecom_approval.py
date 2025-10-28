#!/usr/bin/env python3
"""
企业微信审批API端点
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ....database import get_db
from ....services.wecom_approval_service import WeComApprovalService, WeComApprovalCallbackHandler
from ....services.wecom_integration import WeComApprovalIntegration
from ....auth_routes import get_current_user
from ....models import User

# 请求数据模型
class ApprovalActionRequest(BaseModel):
    comments: Optional[str] = None
    modified_data: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None

class ForwardRequest(ApprovalActionRequest):
    forwarded_to_id: int
    forward_reason: str

class RequestInputRequest(ApprovalActionRequest):
    input_deadline: Optional[str] = None  # ISO datetime string

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


# ======================== 新增：6种审批动作API ========================

@router.post("/approve/{quote_id}")
async def approve_quote(
    quote_id: int,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批准报价单
    """
    service = WeComApprovalService(db)
    try:
        result = service.approve_quote(
            quote_id=quote_id,
            approver_id=current_user.id,
            comments=request.comments
        )
        return {
            "message": "报价单已批准",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject/{quote_id}")
async def reject_quote(
    quote_id: int,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    拒绝报价单
    """
    if not request.comments:
        raise HTTPException(status_code=400, detail="拒绝时必须提供拒绝原因")
    
    service = WeComApprovalService(db)
    try:
        result = service.reject_quote(
            quote_id=quote_id,
            approver_id=current_user.id,
            comments=request.comments
        )
        return {
            "message": "报价单已拒绝",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve-with-changes/{quote_id}")
async def approve_with_changes(
    quote_id: int,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    修改后批准
    """
    if not request.modified_data:
        raise HTTPException(status_code=400, detail="修改后批准必须提供修改数据")
    
    service = WeComApprovalService(db)
    try:
        result = service.approve_with_changes(
            quote_id=quote_id,
            approver_id=current_user.id,
            comments=request.comments,
            modified_data=request.modified_data,
            change_summary=request.change_summary
        )
        return {
            "message": "报价单已修改并批准",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/return-for-revision/{quote_id}")
async def return_for_revision(
    quote_id: int,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    退回修改
    """
    if not request.comments:
        raise HTTPException(status_code=400, detail="退回修改时必须提供修改建议")
    
    service = WeComApprovalService(db)
    try:
        result = service.return_for_revision(
            quote_id=quote_id,
            approver_id=current_user.id,
            comments=request.comments,
            change_summary=request.change_summary
        )
        return {
            "message": "报价单已退回修改",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forward/{quote_id}")
async def forward_quote(
    quote_id: int,
    request: ForwardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    转交审批
    """
    service = WeComApprovalService(db)
    try:
        result = service.forward_approval(
            quote_id=quote_id,
            approver_id=current_user.id,
            forwarded_to_id=request.forwarded_to_id,
            forward_reason=request.forward_reason,
            comments=request.comments
        )
        return {
            "message": "审批已转交",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request-input/{quote_id}")
async def request_input(
    quote_id: int,
    request: RequestInputRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    征求意见
    """
    if not request.comments:
        raise HTTPException(status_code=400, detail="征求意见时必须说明需要什么信息")
    
    service = WeComApprovalService(db)
    try:
        result = service.request_input(
            quote_id=quote_id,
            approver_id=current_user.id,
            comments=request.comments,
            input_deadline=request.input_deadline
        )
        return {
            "message": "已征求意见",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================== 审批链接相关API ========================

@router.get("/approval-link/{token}")
async def get_approval_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    通过审批链接Token获取报价单信息（企业微信回调使用）
    """
    service = WeComApprovalService(db)
    try:
        quote_info = service.get_quote_by_approval_token(token)
        return quote_info
    except Exception as e:
        raise HTTPException(status_code=404, detail="审批链接无效或已过期")


@router.post("/generate-approval-link/{quote_id}")
async def generate_approval_link(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成审批链接
    """
    service = WeComApprovalService(db)
    try:
        link_info = service.generate_approval_link(quote_id, current_user.id)
        return {
            "message": "审批链接已生成",
            "approval_link": link_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 企业微信集成端点 ====================

@router.post("/create-wecom-approval/{quote_id}")
async def create_wecom_approval(
    quote_id: int,
    approver_userid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建企业微信审批申请
    """
    integration = WeComApprovalIntegration(db)
    try:
        result = await integration.create_approval(quote_id, approver_userid)
        return {
            "message": "企业微信审批申请已创建",
            "sp_no": result.get("sp_no")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-notification/{quote_id}")
async def send_approval_notification(
    quote_id: int,
    approver_userid: str,
    message_type: str = "pending",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送企业微信审批通知
    """
    integration = WeComApprovalIntegration(db)
    try:
        success = await integration.send_approval_notification(
            quote_id=quote_id,
            approver_userid=approver_userid,
            message_type=message_type
        )
        if success:
            return {"message": "通知发送成功"}
        else:
            return {"message": "通知发送失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-status/{quote_id}")
async def sync_approval_status(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步企业微信审批状态
    """
    integration = WeComApprovalIntegration(db)
    try:
        result = await integration.sync_approval_status(quote_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wecom-detail/{sp_no}")
async def get_wecom_approval_detail(
    sp_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取企业微信审批单详情
    """
    integration = WeComApprovalIntegration(db)
    try:
        result = await integration.get_approval_detail(sp_no)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))