"""
超级管理员认证模块
独立于企业微信认证系统的超级管理员登录
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT设置
SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "super-admin-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# 预设的超级管理员账户（生产环境中应该从环境变量或数据库读取）
SUPER_ADMIN_CREDENTIALS = {
    "admin": "$2b$12$4ap086ZEO8w1ioFXwGbHEuI2VIoC138bQr5VruRvL2Gh6LDzIGPC."  # "admin123"的bcrypt哈希
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_admin_token(username: str) -> str:
    """创建管理员JWT令牌"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": username,
        "exp": expire,
        "type": "admin"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_admin_token(token: str) -> Optional[dict]:
    """验证管理员JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "admin":
            return None
            
        return {"username": username}
    except JWTError:
        return None

def authenticate_admin(username: str, password: str) -> bool:
    """验证超级管理员凭据"""
    if username not in SUPER_ADMIN_CREDENTIALS:
        return False
    
    hashed_password = SUPER_ADMIN_CREDENTIALS[username]
    return verify_password(password, hashed_password)

def create_admin_account(username: str, password: str) -> str:
    """创建新的管理员账户（返回密码哈希，用于添加到配置中）"""
    return get_password_hash(password)

# 用于生成新密码哈希的工具函数
if __name__ == "__main__":
    # 生成默认密码的哈希
    print("admin123的哈希:", get_password_hash("admin123"))