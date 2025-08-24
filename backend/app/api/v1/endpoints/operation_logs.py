from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db
from app.models import User
from app.auth_routes import get_current_user
from app.middleware.permissions import (
    require_user_permission, 
    require_manager_permission, 
    require_admin_permission
)

router = APIRouter(prefix="/operation-logs", tags=["operation-logs"])


@router.get("/", response_model=List[schemas.OperationLog])
def get_operation_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取操作日志列表 - 根据角色返回不同范围的日志"""
    if current_user.role == "user":
        # 一般用户只能查看自己的操作日志
        logs = crud.get_operation_logs(db, skip=skip, limit=limit, user_id=current_user.id)
    elif current_user.role == "manager":
        # 销售经理可以查看所有操作日志（有限权限）
        require_manager_permission()(current_user)
        logs = crud.get_operation_logs(db, skip=skip, limit=limit)
    else:
        # 管理员及以上可以查看所有操作日志
        require_admin_permission()(current_user)
        logs = crud.get_operation_logs(db, skip=skip, limit=limit)
    
    return logs


@router.get("/my", response_model=List[schemas.OperationLog])
def get_my_operation_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的操作日志 - 所有用户"""
    require_user_permission()(current_user)
    logs = crud.get_operation_logs(db, skip=skip, limit=limit, user_id=current_user.id)
    return logs


@router.get("/user/{user_id}", response_model=List[schemas.OperationLog])
def get_user_operation_logs(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定用户的操作日志 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    # 检查目标用户是否存在
    target_user = crud.get_user(db, user_id=user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logs = crud.get_operation_logs(db, skip=skip, limit=limit, user_id=user_id)
    return logs