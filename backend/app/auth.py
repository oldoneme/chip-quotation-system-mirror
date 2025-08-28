"""
认证和授权模块
临时实现用于测试API
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户
    临时实现：如果没有提供token，返回默认测试用户
    """
    
    # 如果提供了token，尝试解析（这里简化处理）
    if credentials:
        # TODO: 实现真实的token验证逻辑
        # 目前简单检查token是否是"test"
        if credentials.credentials == "test":
            user = db.query(User).filter(User.userid == "test_user_001").first()
            if user:
                return user
    
    # 如果没有token或token无效，返回第一个现有用户（兼容模式）
    user = db.query(User).first()
    if not user:
        # 如果没有用户，说明需要先通过企业微信登录
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先通过企业微信登录创建用户"
        )
    
    return user


def require_role(required_role: str):
    """
    需要特定角色的装饰器
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        role_hierarchy = {
            'user': 1,
            'manager': 2,
            'admin': 3,
            'super_admin': 4
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 99)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return current_user
    
    return role_checker


def require_admin():
    """需要管理员权限"""
    return require_role('admin')


def require_super_admin():
    """需要超级管理员权限"""
    return require_role('super_admin')