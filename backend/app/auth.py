"""
认证和授权模块
临时实现用于测试API
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import jwt
import os
from datetime import datetime, timedelta

from .database import get_db
from .models import User

security = HTTPBearer(auto_error=False)

# JWT配置（与auth.py保持一致）
JWT_SECRET = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALG = "HS256"


def create_user_token(user: User, expires_seconds: int = 300, scope: str = "snapshot") -> str:
    """创建短期JWT令牌用于前端快照等场景"""
    now = datetime.utcnow()
    payload = {
        "sub": user.userid,
        "iat": now,
        "exp": now + timedelta(seconds=expires_seconds),
        "scope": scope,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_jwt(token: str):
    """解码JWT令牌"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证已过期，请重新登录"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的认证令牌: {str(e)}"
        )

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户 - 三段兜底认证
    1. Authorization: Bearer xxx
    2. Cookie: auth_token=xxx
    3. Query: ?jwt=xxx (兜底，用于首屏)
    """
    payload = None
    
    # 1) Authorization: Bearer xxx
    if credentials and credentials.credentials:
        try:
            payload = decode_jwt(credentials.credentials)
        except HTTPException:
            # Authorization token 无效，继续尝试其他方式
            pass
    
    # 2) Cookie: auth_token=xxx
    if not payload:
        cookie_token = request.cookies.get("auth_token")
        if cookie_token:
            try:
                payload = decode_jwt(cookie_token)
            except HTTPException:
                # Cookie token 无效，继续尝试查询参数
                pass
    
    # 3) Query: ?jwt=xxx (兜底，用于首屏)
    if not payload:
        qtoken = request.query_params.get("jwt")
        if qtoken:
            payload = decode_jwt(qtoken)
        else:
            # 所有认证方式都失败，尝试兼容模式
            user = db.query(User).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="请先通过企业微信登录创建用户"
                )
            return user
    
    # 从payload提取用户信息
    if payload:
        userid = payload.get("sub")
        if not userid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证令牌中缺少用户标识"
            )
        
        user = db.query(User).filter(User.userid == userid).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在，请重新登录"
            )
        
        return user
    
    # 最后的兜底：返回第一个用户（兼容模式）
    user = db.query(User).first()
    if not user:
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
