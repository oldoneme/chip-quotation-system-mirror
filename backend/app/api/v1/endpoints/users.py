from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import logging
from ....database import get_db
from ....models import User
from ....auth_schemas import UserResponse
from ....admin_auth import require_admin_auth

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_all_users(
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_auth)
):
    """获取所有用户列表 - 仅管理员可访问"""
    
    try:
        users = db.query(User).filter(User.is_active == True).all()
        return [
            {
                "id": user.id,
                "userid": user.userid,
                "name": user.name,
                "mobile": user.mobile,
                "email": user.email,
                "department": user.department,
                "position": user.position,
                "role": user.role,
                "is_active": user.is_active,
                "avatar": user.avatar,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login": user.last_login
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_auth)
):
    """更新用户角色 - 仅管理员可操作"""
    
    # 验证角色是否有效
    valid_roles = ["admin", "manager", "user"]
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"无效角色，允许的角色：{', '.join(valid_roles)}")
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 独立管理员系统不需要此限制
        
        old_role = user.role
        user.role = new_role
        db.commit()
        
        admin_name = admin.get("username", "独立管理员")
        logger.info(f"管理员 {admin_name} 将用户 {user.name} 的角色从 {old_role} 修改为 {new_role}")
        
        return {
            "message": f"用户 {user.name} 的角色已更新为 {new_role}",
            "user_id": user_id,
            "old_role": old_role,
            "new_role": new_role
        }
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新用户角色失败")

@router.put("/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_auth)
):
    """更新用户状态（启用/禁用）- 仅管理员可操作"""
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 独立管理员系统不需要此限制
        
        old_status = user.is_active
        user.is_active = is_active
        db.commit()
        
        status_text = "启用" if is_active else "禁用"
        admin_name = admin.get("username", "独立管理员")
        logger.info(f"管理员 {admin_name} {status_text}了用户 {user.name}")
        
        return {
            "message": f"用户 {user.name} 已{status_text}",
            "user_id": user_id,
            "is_active": is_active
        }
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新用户状态失败")

@router.get("/stats")
async def get_user_stats(
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_auth)
):
    """获取用户统计信息 - 仅管理员可访问"""
    
    try:
        total_users = db.query(User).filter(User.is_active == True).count()
        admin_count = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        manager_count = db.query(User).filter(User.role == "manager", User.is_active == True).count()
        user_count = db.query(User).filter(User.role == "user", User.is_active == True).count()
        
        return {
            "total_users": total_users,
            "role_distribution": {
                "admin": admin_count,
                "manager": manager_count,
                "user": user_count
            }
        }
    except Exception as e:
        logger.error(f"获取用户统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户统计信息失败")