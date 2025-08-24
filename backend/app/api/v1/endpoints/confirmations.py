from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models import User
from app.auth_routes import get_current_user
from app.middleware.permissions import require_admin_permission, require_user_permission
from app.middleware.confirmation import get_confirmation_manager, ConfirmationManager, SENSITIVE_OPERATIONS
from pydantic import BaseModel

router = APIRouter(prefix="/confirmations", tags=["confirmations"])

# Pydantic模型
class ConfirmationRequest(BaseModel):
    operation: str
    operation_data: Dict[str, Any]

class ConfirmationResponse(BaseModel):
    password_confirmation: str
    additional_data: Dict[str, Any] = {}

class AdminApprovalRequest(BaseModel):
    action: str  # 'approve' or 'reject'
    reason: str = ""

@router.post("/request")
def request_confirmation(
    confirmation_request: ConfirmationRequest,
    current_user: User = Depends(get_current_user),
    confirmation_manager: ConfirmationManager = Depends(get_confirmation_manager)
):
    """请求操作确认"""
    require_user_permission()(current_user)
    
    try:
        confirmation_info = confirmation_manager.create_confirmation(
            confirmation_request.operation,
            current_user,
            confirmation_request.operation_data
        )
        
        return {
            "success": True,
            "message": "确认请求已创建",
            **confirmation_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm/{token}")
def confirm_operation(
    token: str,
    confirmation_response: ConfirmationResponse,
    current_user: User = Depends(get_current_user),
    confirmation_manager: ConfirmationManager = Depends(get_confirmation_manager)
):
    """确认操作"""
    require_user_permission()(current_user)
    
    try:
        confirmation_data = {
            'password_confirmation': confirmation_response.password_confirmation,
            **confirmation_response.additional_data
        }
        
        result = confirmation_manager.confirm_operation(
            token,
            current_user,
            confirmation_data
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/approve/{token}")
def admin_approve_operation(
    token: str,
    approval_request: AdminApprovalRequest,
    current_user: User = Depends(get_current_user),
    confirmation_manager: ConfirmationManager = Depends(get_confirmation_manager)
):
    """管理员批准/拒绝操作"""
    require_admin_permission()(current_user)
    
    try:
        approval_data = {
            'action': approval_request.action,
            'reason': approval_request.reason
        }
        
        result = confirmation_manager.admin_approve_operation(
            token,
            current_user,
            approval_data
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pending")
def get_pending_confirmations(
    current_user: User = Depends(get_current_user),
    confirmation_manager: ConfirmationManager = Depends(get_confirmation_manager)
):
    """获取用户的待确认操作"""
    require_user_permission()(current_user)
    
    confirmations = confirmation_manager.get_pending_confirmations(current_user)
    
    return {
        "success": True,
        "confirmations": confirmations,
        "count": len(confirmations)
    }

@router.get("/admin/pending")
def get_admin_pending_confirmations(
    current_user: User = Depends(get_current_user),
    confirmation_manager: ConfirmationManager = Depends(get_confirmation_manager)
):
    """获取需要管理员批准的操作"""
    require_admin_permission()(current_user)
    
    confirmations = confirmation_manager.get_pending_confirmations(
        current_user, 
        admin_only=True
    )
    
    return {
        "success": True,
        "confirmations": confirmations,
        "count": len(confirmations)
    }

@router.get("/operations")
def get_sensitive_operations(
    current_user: User = Depends(get_current_user)
):
    """获取敏感操作列表"""
    require_user_permission()(current_user)
    
    operations = []
    for operation_key, operation_config in SENSITIVE_OPERATIONS.items():
        operations.append({
            "operation": operation_key,
            "name": operation_config["name"],
            "description": operation_config["description"],
            "risk_level": operation_config["risk_level"],
            "timeout_seconds": operation_config["confirmation_timeout"],
            "admin_approval_required": operation_config["admin_approval"],
            "required_fields": operation_config["required_fields"]
        })
    
    return {
        "success": True,
        "operations": operations
    }

@router.delete("/cleanup")
def cleanup_expired_confirmations(
    current_user: User = Depends(get_current_user),
    confirmation_manager: ConfirmationManager = Depends(get_confirmation_manager)
):
    """清理过期的确认（管理员操作）"""
    require_admin_permission()(current_user)
    
    cleaned_count = confirmation_manager.cleanup_expired_confirmations()
    
    return {
        "success": True,
        "message": f"已清理 {cleaned_count} 个过期的确认",
        "cleaned_count": cleaned_count
    }