"""
企业微信认证端点
处理企业微信OAuth授权和用户认证
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import quote, unquote
import logging
import json

from ....database import get_db
from ....wecom_auth import WeComOAuth as WeComAuth
from ....models import User
# 导入认证依赖和Schema
from app.auth_routes import get_current_user
from app.auth_schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["认证"])

# 初始化企业微信认证
wecom_auth = WeComAuth()

@router.get("/whoami", response_model=UserResponse)
async def whoami(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息 (兼容前端调用 /api/v1/auth/whoami)
    """
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

@router.get("/callback")
async def auth_callback(
    code: str = Query(..., description="企业微信授权码"),
    state: str = Query(None, description="状态参数"),
    db: Session = Depends(get_db)
):
    """
    企业微信OAuth回调处理
    处理用户授权并重定向到目标页面
    """
    try:
        # 获取用户信息
        user_info = wecom_auth.get_user_info_by_code(code)
        
        # 查找或创建用户
        user = db.query(User).filter(User.userid == user_info.userid).first()
        if not user:
            # 创建新用户
            user = User(
                userid=user_info.userid,
                name=user_info.name,
                mobile=user_info.mobile,
                email=user_info.email,
                department=user_info.department,
                position=user_info.position
            )
            db.add(user)
            db.commit()
        
        # 解析state参数，确定重定向目标
        if state and state.startswith("quote_detail_"):
            # 提取报价单ID
            quote_id = state.replace("quote_detail_", "")
            # 重定向到报价单详情页面（注意：前端使用BrowserRouter，不需要#）
            redirect_url = f"/quote-detail/{quote_id}?userid={user_info.userid}"
        else:
            # 默认重定向到首页
            redirect_url = f"/?userid={user_info.userid}"
        
        # 构建完整的重定向URL（使用环境变量中的前端地址）
        from app.config import settings
        base_url = settings.FRONTEND_BASE_URL if hasattr(settings, 'FRONTEND_BASE_URL') else "http://localhost:3000"
        full_redirect_url = f"{base_url}{redirect_url}"
        
        return RedirectResponse(url=full_redirect_url)
        
    except Exception as e:
        logging.error(f"认证回调失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"认证失败: {str(e)}")


@router.get("/login")
async def login_redirect(
    redirect_path: str = Query("/", description="登录后重定向路径")
):
    """
    生成企业微信登录链接
    """
    # URL编码重定向路径
    encoded_redirect = quote(redirect_path)
    
    # 构建OAuth授权URL - 使用环境变量中的API基础URL
    from app.config import settings
    api_base_url = settings.API_BASE_URL if hasattr(settings, 'API_BASE_URL') else "http://localhost:8000"
    callback_url = f"{api_base_url}/v1/auth/callback"
    oauth_url = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={wecom_auth.corp_id}&redirect_uri={quote(callback_url)}&response_type=code&scope=snsapi_base&state={encoded_redirect}"
    
    return {"login_url": oauth_url}