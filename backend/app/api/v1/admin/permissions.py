"""
管理员权限控制中间件
"""

from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

from ....auth_routes import get_current_user
from ....database import get_db
from ....models import User


def require_admin_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    要求admin或super_admin角色
    用于管理员专用接口的权限控制
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录"
        )

    if current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user


def require_super_admin_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    要求super_admin角色
    用于高危险操作（如硬删除）
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录"
        )

    if current_user.role != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    return current_user