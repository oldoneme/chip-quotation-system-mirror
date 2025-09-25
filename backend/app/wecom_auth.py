#!/usr/bin/env python3
"""
企业微信OAuth认证模块
"""
import os
import json
import secrets
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .config import settings

from .models import User, UserSession, Department
from .auth_schemas import WeComUserInfo, UserCreate, UserResponse


class WeComOAuth:
    """企业微信OAuth认证类"""
    
    def __init__(self):
        self.corp_id = settings.WECOM_CORP_ID
        self.agent_id = str(settings.WECOM_AGENT_ID) if settings.WECOM_AGENT_ID is not None else ""
        self.corp_secret = settings.WECOM_CORP_SECRET or settings.WECOM_SECRET
        self.redirect_uri = settings.WECOM_CALLBACK_URL.rstrip("/") + "/auth/callback"
        
        # API端点
        self.token_url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        self.user_info_url = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"
        self.user_detail_url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        self.dept_list_url = "https://qyapi.weixin.qq.com/cgi-bin/department/list"
        
        # Access Token缓存
        self._access_token = None
        self._token_expires_at = None
    
    def get_authorize_url(self, state: str = None) -> str:
        """
        生成企业微信OAuth授权URL
        
        Args:
            state: 状态参数，用于防CSRF攻击
            
        Returns:
            授权URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "appid": self.corp_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "snsapi_base",
            "agentid": self.agent_id,
            "state": state
        }
        
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        # 企业微信网页授权URL - 在企业微信内部使用
        return f"https://open.weixin.qq.com/connect/oauth2/authorize?{param_str}#wechat_redirect"
    
    def get_access_token(self) -> str:
        """
        获取访问令牌（带缓存）
        
        Returns:
            Access Token
        """
        # 检查缓存
        if (self._access_token and self._token_expires_at and 
            datetime.now() < self._token_expires_at):
            return self._access_token
        
        # 请求新的token
        response = requests.get(self.token_url, params={
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        })
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get access token")
        
        data = response.json()
        if data.get("errcode", 0) != 0:
            raise HTTPException(status_code=500, detail=f"WeChat API error: {data.get('errmsg')}")
        
        # 缓存token（提前10分钟过期）
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 7200) - 600
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        return self._access_token
    
    def get_user_info_by_code(self, code: str) -> WeComUserInfo:
        """
        通过授权码获取用户信息
        
        Args:
            code: 授权码
            
        Returns:
            用户信息
        """
        access_token = self.get_access_token()
        
        # 1. 通过code获取用户ID
        response = requests.get(self.user_info_url, params={
            "access_token": access_token,
            "code": code
        })
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get user info")
        
        data = response.json()
        if data.get("errcode", 0) != 0:
            raise HTTPException(status_code=500, detail=f"WeChat API error: {data.get('errmsg')}")
        
        userid = data.get("UserId")
        if not userid:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        # 2. 获取用户详细信息
        return self.get_user_detail(userid)
    
    def get_user_detail(self, userid: str) -> WeComUserInfo:
        """
        获取用户详细信息
        
        Args:
            userid: 企业微信用户ID
            
        Returns:
            用户详细信息
        """
        access_token = self.get_access_token()
        
        response = requests.get(self.user_detail_url, params={
            "access_token": access_token,
            "userid": userid
        })
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get user detail")
        
        data = response.json()
        if data.get("errcode", 0) != 0:
            raise HTTPException(status_code=500, detail=f"WeChat API error: {data.get('errmsg')}")
        
        return WeComUserInfo(**data)
    
    def sync_departments(self, db: Session) -> int:
        """
        同步企业微信部门信息
        
        Args:
            db: 数据库会话
            
        Returns:
            同步的部门数量
        """
        access_token = self.get_access_token()
        
        response = requests.get(self.dept_list_url, params={
            "access_token": access_token
        })
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get department list")
        
        data = response.json()
        if data.get("errcode", 0) != 0:
            raise HTTPException(status_code=500, detail=f"WeChat API error: {data.get('errmsg')}")
        
        departments = data.get("department", [])
        synced_count = 0
        
        for dept_data in departments:
            dept_id = dept_data["id"]
            
            # 查找现有部门
            existing_dept = db.query(Department).filter(Department.dept_id == dept_id).first()
            
            if existing_dept:
                # 更新现有部门
                existing_dept.name = dept_data["name"]
                existing_dept.parent_id = dept_data.get("parentid")
                existing_dept.order = dept_data.get("order", 0)
                existing_dept.updated_at = datetime.utcnow()
            else:
                # 创建新部门
                new_dept = Department(
                    dept_id=dept_id,
                    name=dept_data["name"],
                    parent_id=dept_data.get("parentid"),
                    order=dept_data.get("order", 0),
                    is_allowed=False  # 默认不允许访问
                )
                db.add(new_dept)
            
            synced_count += 1
        
        db.commit()
        return synced_count


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.wecom = WeComOAuth()
    
    def create_or_update_user(self, wecom_user: WeComUserInfo) -> User:
        """
        创建或更新用户
        
        Args:
            wecom_user: 企业微信用户信息
            
        Returns:
            用户对象
        """
        # 查找现有用户
        user = self.db.query(User).filter(User.userid == wecom_user.userid).first()
        
        if user:
            # 更新现有用户
            user.name = wecom_user.name
            user.mobile = wecom_user.mobile
            user.email = wecom_user.email
            user.position = wecom_user.position
            user.avatar = wecom_user.avatar
            user.department_ids = json.dumps(wecom_user.department or [])
            user.is_leader_in_dept = json.dumps(wecom_user.is_leader_in_dept or [])
            user.direct_leader = json.dumps(wecom_user.direct_leader or [])
            user.updated_at = datetime.utcnow()
            user.last_login = datetime.utcnow()
        else:
            # 创建新用户
            user = User(
                userid=wecom_user.userid,
                name=wecom_user.name,
                mobile=wecom_user.mobile,
                email=wecom_user.email,
                position=wecom_user.position,
                role="user",  # 默认角色
                avatar=wecom_user.avatar,
                department_ids=json.dumps(wecom_user.department or []),
                is_leader_in_dept=json.dumps(wecom_user.is_leader_in_dept or []),
                direct_leader=json.dumps(wecom_user.direct_leader or []),
                last_login=datetime.utcnow()
            )
            self.db.add(user)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def check_user_permission(self, user: User) -> bool:
        """
        检查用户权限
        
        Args:
            user: 用户对象
            
        Returns:
            是否有权限访问
        """
        # 检查用户是否激活
        if not user.is_active:
            return False
        
        # 管理员总是有权限
        if user.role == "admin":
            return True
        
        # 检查部门权限
        try:
            user_dept_ids = json.loads(user.department_ids or "[]")
            
            # 如果用户没有部门信息，默认允许访问（适用于企业微信单部门或小企业）
            if not user_dept_ids:
                print(f"用户 {user.name} 没有部门信息，默认允许访问")
                return True
                
            allowed_depts = self.db.query(Department).filter(
                Department.dept_id.in_(user_dept_ids),
                Department.is_allowed == True
            ).all()
            
            return len(allowed_depts) > 0
        except (json.JSONDecodeError, TypeError):
            print(f"用户 {user.name} 部门权限解析失败，默认允许访问")
            return True
    
    def create_session(self, user: User, user_agent: str = None, ip_address: str = None) -> UserSession:
        """
        创建用户会话
        
        Args:
            user: 用户对象
            user_agent: 浏览器信息
            ip_address: IP地址
            
        Returns:
            会话对象
        """
        # 生成会话令牌
        session_token = secrets.token_urlsafe(32)
        
        # 设置过期时间（7天）
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # 创建会话
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_user_by_session_token(self, session_token: str) -> Optional[User]:
        """
        通过会话令牌获取用户
        
        Args:
            session_token: 会话令牌
            
        Returns:
            用户对象或None
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            return None
        
        return session.user
    
    def get_session_by_token(self, session_token: str) -> Optional[UserSession]:
        """
        通过会话令牌获取会话对象
        
        Args:
            session_token: 会话令牌
            
        Returns:
            会话对象或None
        """
        return self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        使会话失效
        
        Args:
            session_token: 会话令牌
            
        Returns:
            是否成功
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            return True
        
        return False