"""
企业微信认证端点
处理企业微信OAuth授权和用户认证
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import quote, unquote
import logging

from ....database import get_db
from ....wecom_auth import WeComOAuth as WeComAuth
from ....models import User

router = APIRouter(prefix="/auth", tags=["认证"])

# 初始化企业微信认证
wecom_auth = WeComAuth()

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
            # 重定向到报价单详情页面
            redirect_url = f"/#/quote-detail/{quote_id}?userid={user_info.userid}"
        else:
            # 默认重定向到首页
            redirect_url = f"/?userid={user_info.userid}"
        
        # 构建完整的重定向URL（包含域名）
        base_url = "http://127.0.0.1:3000"  # 前端地址
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
    
    # 构建OAuth授权URL
    callback_url = "http://127.0.0.1:8000/api/v1/auth/callback"
    oauth_url = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={wecom_auth.corp_id}&redirect_uri={quote(callback_url)}&response_type=code&scope=snsapi_base&state={encoded_redirect}"
    
    return {"login_url": oauth_url}