from fastapi import APIRouter, HTTPException, Response, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from datetime import timedelta
import logging
from .admin_auth import (
    verify_admin_password, 
    create_admin_access_token, 
    ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_admin,
    require_admin_auth
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def admin_login(response: Response, login_data: AdminLoginRequest):
    """管理员登录"""
    if not verify_admin_password(login_data.username, login_data.password):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_admin_access_token(
        data={"sub": login_data.username}, 
        expires_delta=access_token_expires
    )
    
    # 设置 Cookie
    response.set_cookie(
        key="admin_token",
        value=access_token,
        max_age=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=True,  # HTTPS 环境
        samesite="lax"
    )
    
    logger.info(f"管理员 {login_data.username} 登录成功")
    
    return {
        "message": "登录成功",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/logout")
async def admin_logout(response: Response):
    """管理员登出"""
    response.delete_cookie("admin_token")
    return {"message": "已退出登录"}

@router.get("/me")
async def get_admin_info(current_admin: dict = Depends(require_admin_auth)):
    """获取当前管理员信息"""
    return {
        "username": current_admin["username"],
        "role": "admin",
        "authenticated": True
    }

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """管理员登录页面"""
    # 检查是否已经登录
    try:
        admin_token = request.cookies.get("admin_token")
        if admin_token:
            from .admin_auth import verify_admin_token
            if verify_admin_token(admin_token):
                return RedirectResponse(url="/user-management", status_code=302)
    except:
        pass
    
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理员登录 - 芯片测试报价系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .login-header h1 {
            color: #333;
            margin: 0 0 8px 0;
            font-size: 24px;
        }
        
        .login-header p {
            color: #666;
            margin: 0;
            font-size: 14px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .login-button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            transition: opacity 0.3s;
        }
        
        .login-button:hover {
            opacity: 0.9;
        }
        
        .login-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .error-message {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 6px;
            padding: 12px;
            color: #c53030;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        
        .security-notice {
            background: #fef6e7;
            border: 1px solid #f6d55c;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #92400e;
        }
        
        .security-notice strong {
            color: #d97706;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>管理员登录</h1>
            <p>芯片测试报价系统</p>
        </div>
        
        <div class="security-notice">
            <strong>⚠️ 安全提醒：</strong>请输入管理员账号和密码
        </div>
        
        <div class="error-message" id="errorMessage"></div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="login-button" id="loginButton">
                登录
            </button>
        </form>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const button = document.getElementById('loginButton');
            const errorMessage = document.getElementById('errorMessage');
            
            button.disabled = true;
            button.textContent = '登录中...';
            errorMessage.style.display = 'none';
            
            const formData = {
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };
            
            try {
                const response = await fetch('/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // 登录成功，跳转到用户管理页面
                    window.location.href = '/user-management';
                } else {
                    // 登录失败，显示错误消息
                    errorMessage.textContent = result.detail || '登录失败';
                    errorMessage.style.display = 'block';
                }
            } catch (error) {
                errorMessage.textContent = '网络错误，请稍后重试';
                errorMessage.style.display = 'block';
            } finally {
                button.disabled = false;
                button.textContent = '登录';
            }
        });
    </script>
</body>
</html>
    """)

