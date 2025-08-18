#!/usr/bin/env python3
"""
认证相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    userid: str
    name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    avatar: Optional[str] = None


class UserCreate(UserBase):
    """创建用户模型"""
    department_ids: Optional[str] = None
    is_leader_in_dept: Optional[str] = None
    direct_leader: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户模型"""
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    avatar: Optional[str] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    department_ids: Optional[List[int]] = None
    is_leader_in_dept: Optional[List[bool]] = None
    direct_leader: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserSessionCreate(BaseModel):
    """创建会话模型"""
    user_id: int
    session_token: str
    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class UserSessionResponse(BaseModel):
    """会话响应模型"""
    id: int
    session_token: str
    expires_at: datetime
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    """部门基础模型"""
    dept_id: int
    name: str
    parent_id: Optional[int] = None
    order: int = 0
    is_allowed: bool = False


class DepartmentCreate(DepartmentBase):
    """创建部门模型"""
    pass


class DepartmentResponse(DepartmentBase):
    """部门响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应模型"""
    user: UserResponse
    session_token: str
    expires_at: datetime


class WeComUserInfo(BaseModel):
    """企业微信用户信息模型"""
    userid: str
    name: str
    mobile: Optional[str] = None
    department: Optional[List[int]] = None
    position: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    telephone: Optional[str] = None
    alias: Optional[str] = None
    extattr: Optional[dict] = None
    status: Optional[int] = None
    qr_code: Optional[str] = None
    external_position: Optional[str] = None
    external_profile: Optional[dict] = None
    is_leader_in_dept: Optional[List[int]] = None
    direct_leader: Optional[List[str]] = None