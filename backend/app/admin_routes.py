"""
超级管理员路由
提供独立的管理员登录和用户管理功能
"""
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import logging

from .database import get_db
from .models import User
from .schemas import User as UserSchema, UserUpdate
from .admin_auth import authenticate_admin, create_admin_token, verify_admin_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    message: str

def require_admin_auth(request: Request):
    """验证管理员身份的依赖函数"""
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    
    admin_info = verify_admin_token(token)
    if not admin_info:
        raise HTTPException(status_code=401, detail="登录已过期")
    
    return admin_info

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page():
    """超级管理员登录页面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>超级管理员登录 - 芯片测试报价系统</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            padding: 40px;
            width: 100%;
            max-width: 400px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .login-header h1 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 24px;
        }
        .login-header p {
            margin: 0;
            color: #666;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-size: 14px;
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
        }
        .login-button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.3s;
        }
        .login-button:hover {
            opacity: 0.9;
        }
        .login-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .error-message {
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>超级管理员登录</h1>
            <p>芯片测试报价系统</p>
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
                    window.location.href = '/admin/management';
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
"""

@router.post("/login")
async def admin_login(request: AdminLoginRequest, response: Response):
    """超级管理员登录"""
    if not authenticate_admin(request.username, request.password):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 创建JWT令牌
    access_token = create_admin_token(request.username)
    
    # 设置HTTP-only cookie
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        secure=False,  # 开发环境设为False，生产环境应设为True
        samesite="lax",
        max_age=8 * 60 * 60  # 8小时
    )
    
    return {"success": True, "message": "登录成功"}

@router.post("/logout")
async def admin_logout(response: Response):
    """超级管理员退出登录"""
    response.delete_cookie("admin_token")
    return {"success": True, "message": "退出成功"}

@router.get("/management", response_class=HTMLResponse)
async def admin_management_page(admin_info: dict = Depends(require_admin_auth)):
    """用户管理页面"""
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户管理 - 芯片测试报价系统</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            margin: 0;
            color: #333;
        }}
        .user-info {{
            color: #666;
        }}
        .logout-btn {{
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 20px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }}
        .btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }}
        .btn:hover {{
            background: #0056b3;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-active {{
            color: #28a745;
        }}
        .status-inactive {{
            color: #dc3545;
        }}
        .role-super_admin {{
            background: #dc3545;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .role-admin {{
            background: #fd7e14;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .role-manager {{
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .role-user {{
            background: #6c757d;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>用户管理系统</h1>
        <div>
            <span class="user-info">欢迎，{admin_info['username']}</span>
            <button class="logout-btn" onclick="logout()">退出登录</button>
        </div>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>企业微信用户管理</h2>
            <button class="btn" onclick="syncUsers()">同步企业微信用户</button>
            <button class="btn" onclick="refreshUsers()">刷新用户列表</button>
            
            <table id="usersTable">
                <thead>
                    <tr>
                        <th>用户ID</th>
                        <th>姓名</th>
                        <th>手机号</th>
                        <th>邮箱</th>
                        <th>部门</th>
                        <th>职位</th>
                        <th>角色</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td colspan="9" style="text-align: center; padding: 40px;">
                            点击"同步企业微信用户"开始获取用户数据
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function logout() {{
            try {{
                await fetch('/admin/logout', {{ method: 'POST' }});
                window.location.href = '/admin/login';
            }} catch (error) {{
                console.error('退出登录失败:', error);
            }}
        }}
        
        async function syncUsers() {{
            try {{
                const response = await fetch('/admin/users/sync', {{ method: 'POST' }});
                const result = await response.json();
                if (response.ok) {{
                    alert('同步成功：' + result.message);
                    refreshUsers();
                }} else {{
                    alert('同步失败：' + result.detail);
                }}
            }} catch (error) {{
                alert('同步失败：网络错误');
            }}
        }}
        
        async function refreshUsers() {{
            try {{
                const response = await fetch('/admin/users');
                const users = await response.json();
                displayUsers(users);
            }} catch (error) {{
                console.error('获取用户列表失败:', error);
            }}
        }}
        
        function displayUsers(users) {{
            const tbody = document.querySelector('#usersTable tbody');
            if (users.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px;">暂无用户数据</td></tr>';
                return;
            }}
            
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${{user.userid}}</td>
                    <td>${{user.name || '-'}}</td>
                    <td>${{user.mobile || '-'}}</td>
                    <td>${{user.email || '-'}}</td>
                    <td>${{user.department || '-'}}</td>
                    <td>${{user.position || '-'}}</td>
                    <td><span class="role-${{user.role}}">${{getRoleText(user.role)}}</span></td>
                    <td class="${{user.is_active ? 'status-active' : 'status-inactive'}}">
                        ${{user.is_active ? '活跃' : '禁用'}}
                    </td>
                    <td>
                        <button class="btn" onclick="changeRole('${{user.userid}}', '${{user.role}}')">修改角色</button>
                        <button class="btn" onclick="toggleStatus('${{user.userid}}', ${{user.is_active}})">
                            ${{user.is_active ? '禁用' : '启用'}}
                        </button>
                    </td>
                </tr>
            `).join('');
        }}
        
        function getRoleText(role) {{
            const roleMap = {{
                'super_admin': '超级管理员',
                'admin': '管理员', 
                'manager': '销售经理',
                'user': '一般用户'
            }};
            return roleMap[role] || role;
        }}
        
        async function changeRole(userid, currentRole) {{
            const roles = [
                {{ value: 'user', text: '一般用户' }},
                {{ value: 'manager', text: '销售经理' }},
                {{ value: 'admin', text: '管理员' }},
                {{ value: 'super_admin', text: '超级管理员' }}
            ];
            
            const options = roles.map(role => 
                `<option value="${{role.value}}" ${{role.value === currentRole ? 'selected' : ''}}>${{role.text}}</option>`
            ).join('');
            
            const newRole = prompt(`请选择新角色：\\n${{roles.map((r, i) => i + 1 + '. ' + r.text).join('\\n')}}\\n\\n输入数字选择：`);
            if (newRole && newRole >= 1 && newRole <= 4) {{
                const selectedRole = roles[newRole - 1].value;
                try {{
                    const response = await fetch(`/admin/users/${{userid}}/role`, {{
                        method: 'PUT',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ role: selectedRole }})
                    }});
                    const result = await response.json();
                    if (response.ok) {{
                        alert('角色修改成功');
                        refreshUsers();
                    }} else {{
                        alert('角色修改失败：' + result.detail);
                    }}
                }} catch (error) {{
                    alert('角色修改失败：网络错误');
                }}
            }}
        }}
        
        async function toggleStatus(userid, currentStatus) {{
            const action = currentStatus ? '禁用' : '启用';
            if (confirm(`确定要${{action}}该用户吗？`)) {{
                try {{
                    const response = await fetch(`/admin/users/${{userid}}/status`, {{
                        method: 'PUT',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ is_active: !currentStatus }})
                    }});
                    const result = await response.json();
                    if (response.ok) {{
                        alert(`用户${{action}}成功`);
                        refreshUsers();
                    }} else {{
                        alert(`用户${{action}}失败：` + result.detail);
                    }}
                }} catch (error) {{
                    alert(`用户${{action}}失败：网络错误`);
                }}
            }}
        }}
    </script>
</body>
</html>
"""

@router.get("/users")
async def get_users(admin_info: dict = Depends(require_admin_auth), db: Session = Depends(get_db)):
    """获取所有用户列表"""
    users = db.query(User).all()
    return users

@router.post("/users/sync")
async def sync_wecom_users(admin_info: dict = Depends(require_admin_auth), db: Session = Depends(get_db)):
    """同步企业微信用户"""
    # 这里将实现企业微信用户同步功能
    return {"success": True, "message": "同步功能正在开发中"}

@router.put("/users/{userid}/role")
async def update_user_role(
    userid: str, 
    role_data: dict,
    admin_info: dict = Depends(require_admin_auth), 
    db: Session = Depends(get_db)
):
    """修改用户角色"""
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    new_role = role_data.get("role")
    if new_role not in ["user", "manager", "admin", "super_admin"]:
        raise HTTPException(status_code=400, detail="无效的角色")
    
    user.role = new_role
    db.commit()
    
    return {"success": True, "message": "角色修改成功"}

@router.put("/users/{userid}/status")
async def update_user_status(
    userid: str,
    status_data: dict,
    admin_info: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db)
):
    """修改用户状态"""
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.is_active = status_data.get("is_active", True)
    db.commit()
    
    return {"success": True, "message": "状态修改成功"}