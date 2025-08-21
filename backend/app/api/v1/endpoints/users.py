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

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.User)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息 - 所有用户"""
    return current_user


@router.put("/me", response_model=schemas.User)
def update_current_user_profile(
    profile_update: schemas.UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新个人信息 - 所有用户"""
    require_user_permission()(current_user)
    
    # 用户只能修改自己的基本信息
    update_data = profile_update.dict(exclude_unset=True)
    updated_user = crud.update_user_profile(db, user_id=current_user.id, update_data=update_data)
    
    # 记录操作日志
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="profile_update",
        details=f"Updated profile fields: {list(update_data.keys())}"
    )
    
    return updated_user


@router.get("/", response_model=List[schemas.User])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有用户列表 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.User)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定用户信息 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserManagementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    updated_user = crud.update_user(db, user_id=user_id, update_data=update_data)
    
    # 记录操作日志
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="user_update",
        details=f"Updated user {user.name}({user.userid}) fields: {list(update_data.keys())}"
    )
    
    return updated_user


@router.put("/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户状态 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_active = status_data.get('is_active')
    if is_active is None:
        raise HTTPException(status_code=400, detail="is_active field is required")
    
    # 防止管理员禁用自己
    if user_id == current_user.id and not is_active:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    
    updated_user = crud.update_user_status(db, user_id=user_id, is_active=is_active)
    
    # 记录操作日志
    action = "enabled" if is_active else "disabled"
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="user_status_change",
        details=f"{action.title()} user {user.name}({user.userid})"
    )
    
    return {
        "success": True,
        "message": f"User {action} successfully",
        "user_id": user_id,
        "new_status": is_active
    }


@router.get("/{user_id}/quotations", response_model=List[schemas.Quotation])
def get_user_quotations(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的报价列表 - 管理员及以上或本人"""
    # 权限检查：管理员可以查看所有人，用户只能查看自己的
    if current_user.role == "user" and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied: Can only view your own quotations")
    
    if current_user.role != "user":
        require_admin_permission()(current_user)
    
    quotations = crud.get_user_quotations(db, user_id=user_id, skip=skip, limit=limit)
    return quotations