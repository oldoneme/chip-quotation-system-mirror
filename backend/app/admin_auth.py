from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import os

# 管理员认证配置
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "your-admin-secret-key-change-in-production")
ADMIN_ALGORITHM = "HS256"
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8小时

# 默认管理员账号 (生产环境应该修改)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"

security = HTTPBearer(auto_error=False)

def verify_admin_password(username: str, password: str) -> bool:
    """验证管理员用户名和密码"""
    # 简单的用户名密码验证
    # 生产环境可以改为从数据库或环境变量读取
    if username == DEFAULT_ADMIN_USERNAME:
        return password == DEFAULT_ADMIN_PASSWORD
    return False

def create_admin_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建管理员访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "admin"})
    encoded_jwt = jwt.encode(to_encode, ADMIN_SECRET_KEY, algorithm=ADMIN_ALGORITHM)
    return encoded_jwt

def verify_admin_token(token: str) -> Optional[dict]:
    """验证管理员令牌"""
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ADMIN_ALGORITHM])
        if payload.get("type") != "admin":
            return None
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username}
    except JWTError:
        return None

async def get_current_admin(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前管理员用户"""
    
    # 优先检查 Authorization header
    if credentials:
        token = credentials.credentials
        admin_info = verify_admin_token(token)
        if admin_info:
            return admin_info
    
    # 检查 Cookie 中的 admin_token
    admin_token = request.cookies.get("admin_token")
    if admin_token:
        admin_info = verify_admin_token(admin_token)
        if admin_info:
            return admin_info
    
    # 未认证
    raise HTTPException(
        status_code=401,
        detail="需要管理员身份认证",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_admin_auth():
    """管理员认证依赖"""
    return Depends(get_current_admin)