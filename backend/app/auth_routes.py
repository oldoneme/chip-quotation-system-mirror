#!/usr/bin/env python3
"""
认证相关的路由
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .wecom_auth import AuthService, WeComOAuth
from .auth_schemas import UserResponse, LoginResponse
from .models import User
from .middleware.session_manager import is_session_invalidated

router = APIRouter()

# 依赖注入
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """获取当前用户"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # 获取会话对象以检查登录时间
    session = auth_service.get_session_by_token(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = session.user
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # 方案2：实时获取最新用户信息（角色更改立即生效）
    # 重新从数据库获取最新的用户信息，确保角色和状态是最新的
    fresh_user = auth_service.db.query(User).filter(User.id == user.id).first()
    if fresh_user:
        user = fresh_user
    
    # 方案1：角色更改需要重新登录（已禁用）
    # 检查会话是否已失效（角色变更后需要重新登录）
    # if is_session_invalidated(user.userid, session.created_at):
    #     # 使当前会话失效
    #     auth_service.invalidate_session(session_token)
    #     raise HTTPException(status_code=401, detail="Session invalidated due to role change. Please login again.")
    
    # 检查权限
    if not auth_service.check_user_permission(user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return user

def get_current_user_optional(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not session_token:
        return None
    
    # 获取会话对象以检查登录时间
    session = auth_service.get_session_by_token(session_token)
    if not session:
        return None
    
    user = session.user
    if not user:
        return None
    
    # 实时获取最新用户信息（角色更改立即生效）
    fresh_user = auth_service.db.query(User).filter(User.id == user.id).first()
    if fresh_user:
        user = fresh_user
    
    # 已禁用：检查会话是否已失效（角色变更后需要重新登录）
    # if is_session_invalidated(user.userid, session.created_at):
    #     # 使当前会话失效
    #     auth_service.invalidate_session(session_token)
    #     return None
    
    # 检查权限
    if not auth_service.check_user_permission(user):
        return None
    
    return user


@router.get("/api/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    # 解析部门信息
    try:
        department_ids = json.loads(current_user.department_ids or "[]")
        is_leader_in_dept = json.loads(current_user.is_leader_in_dept or "[]")
    except (json.JSONDecodeError, TypeError):
        department_ids = []
        is_leader_in_dept = []
    
    return UserResponse(
        id=current_user.id,
        userid=current_user.userid,
        name=current_user.name,
        mobile=current_user.mobile,
        email=current_user.email,
        department=current_user.department,
        position=current_user.position,
        role=current_user.role,
        is_active=current_user.is_active,
        avatar=current_user.avatar,
        department_ids=department_ids,
        is_leader_in_dept=is_leader_in_dept,
        direct_leader=current_user.direct_leader,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get("/auth/login")
async def login(
    request: Request,
    redirect_url: Optional[str] = None,
    from_source: Optional[str] = None,
    mobile: Optional[str] = None
):
    """发起OAuth登录"""
    wecom = WeComOAuth()
    
    # 获取用户代理信息，用于判断移动端
    user_agent = request.headers.get("user-agent", "").lower()
    is_mobile = mobile == "1" or any(device in user_agent for device in [
        "android", "iphone", "ipad", "ipod", "blackberry", "iemobile", "opera mini"
    ])
    is_wecom = from_source == "wecom" or "wxwork" in user_agent or "micromessenger" in user_agent
    
    # 生成状态参数（包含环境信息）
    state_data = {
        "timestamp": datetime.now().isoformat(),
        "redirect_url": redirect_url or "/dashboard",  # 默认跳转到仪表盘
        "is_mobile": is_mobile,
        "is_wecom": is_wecom,
        "user_agent": user_agent[:100]  # 截取前100个字符避免太长
    }
    state = json.dumps(state_data)
    
    # 获取授权URL
    auth_url = wecom.get_authorize_url(state)
    
    # 移动端添加特殊日志
    if is_mobile:
        print(f"📱 移动端登录请求: {user_agent[:50]}...")
    
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/auth/callback")
async def oauth_callback(
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """OAuth回调处理"""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    try:
        # 解析状态参数
        redirect_url = "/dashboard"  # 默认跳转到权限控制仪表盘
        if state:
            try:
                state_data = json.loads(state)
                redirect_url = state_data.get("redirect_url", "/dashboard")
            except json.JSONDecodeError:
                pass
        
        # 获取用户信息
        wecom_user = auth_service.wecom.get_user_info_by_code(code)
        
        # 创建或更新用户
        user = auth_service.create_or_update_user(wecom_user)
        
        # 检查权限
        if not auth_service.check_user_permission(user):
            # 返回无权限页面或错误
            return RedirectResponse(
                url=f"/?error=access_denied&message=您暂无权限访问此系统",
                status_code=302
            )
        
        # 创建会话
        user_agent = request.headers.get("User-Agent", "")
        client_ip = request.client.host if request.client else ""
        session = auth_service.create_session(user, user_agent, client_ip)
        
        # 设置Cookie
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key="session_token",
            value=session.session_token,
            max_age=7 * 24 * 60 * 60,  # 7天
            httponly=True,
            secure=True,  # HTTPS only
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Code: {code}")
        print(f"State: {state}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url=f"/?error=auth_failed&message=登录失败，请重试: {str(e)}",
            status_code=302
        )


@router.post("/auth/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """登出"""
    if session_token:
        auth_service.invalidate_session(session_token)
    
    # 清除Cookie
    response.delete_cookie("session_token")
    
    return {"message": "Logged out successfully"}


@router.get("/auth/status")
async def auth_status(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取认证状态"""
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "userid": current_user.userid,
                "name": current_user.name,
                "role": current_user.role
            }
        }
    else:
        return {"authenticated": False}


# 管理员专用路由
@router.post("/admin/sync-departments")
async def sync_departments(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """同步企业微信部门信息（管理员专用）"""
    # 检查管理员权限
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        count = auth_service.wecom.sync_departments(auth_service.db)
        return {"message": f"Successfully synced {count} departments"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/admin/wecom-users")
async def list_wecom_users(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取用户列表（企业微信管理员专用）"""
    # 检查管理员权限
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    users = auth_service.db.query(User).all()
    return [
        {
            "id": user.id,
            "userid": user.userid,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "last_login": user.last_login
        }
        for user in users
    ]