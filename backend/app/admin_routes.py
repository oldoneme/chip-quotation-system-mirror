"""
超级管理员路由
提供独立的管理员登录和用户管理功能
"""
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi import status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
from datetime import datetime
import os

from .database import get_db
from .models import User
from .schemas import User as UserSchema, UserUpdate
from .admin_auth import authenticate_admin, create_admin_token, verify_admin_token
from .wecom_service import WecomService
from .middleware.session_manager import record_role_change

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

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
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // 登录成功，跳转到用户管理页面
                    window.location.href = '/api/admin/management';
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
async def admin_login(login_request: AdminLoginRequest, request: Request, response: Response):
    """超级管理员登录"""
    if not authenticate_admin(login_request.username, login_request.password):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 创建JWT令牌
    access_token = create_admin_token(login_request.username)
    
    # 设置HTTP-only cookie
    # 检查是否通过HTTPS访问
    is_secure = request.url.scheme == "https"
    
    if "chipinfos.com.cn" in str(request.url.hostname):
        # 生产环境使用域名设置
        response.set_cookie(
            key="admin_token",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=8 * 60 * 60,
            domain=".chipinfos.com.cn"
        )
    else:
        # 开发环境不设置域名
        response.set_cookie(
            key="admin_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=8 * 60 * 60
        )
    
    return {"success": True, "message": "登录成功"}

@router.post("/logout")
async def admin_logout(response: Response):
    """超级管理员退出登录"""
    response.delete_cookie(
        "admin_token",
        domain=".chipinfos.com.cn"
    )
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
        .btn-danger {{
            background: #dc3545;
            color: white;
        }}
        .btn-danger:hover {{
            background: #c82333;
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
            <h2>系统管理功能</h2>
            <button class="btn" onclick="window.open('/', '_blank')" style="background: #28a745;">🏠 前端主应用</button>
            <button class="btn" onclick="window.open('/admin/database-quote-management', '_blank')" style="background: #17a2b8;">📊 报价单数据库管理</button>
        </div>

        <div class="card">
            <h2>企业微信用户管理</h2>
            <button class="btn" onclick="syncUsers()">同步企业微信用户</button>
            <button class="btn" onclick="refreshUsers()">刷新用户列表</button>
            <button class="btn btn-danger" onclick="cleanupTestUsers()">删除测试用户</button>
            
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
                await fetch('/api/admin/logout', {{ 
                    method: 'POST',
                    credentials: 'include' 
                }});
                window.location.href = '/api/admin/login';
            }} catch (error) {{
                console.error('退出登录失败:', error);
            }}
        }}
        
        async function cleanupTestUsers() {{
            if (!confirm('确定要删除所有测试用户吗？\\n这将删除：张三、李四、王五、赵六、孙七\\n此操作不可恢复！')) {{
                return;
            }}
            
            try {{
                const response = await fetch('/api/admin/users/cleanup-test', {{
                    method: 'POST',
                    credentials: 'include'
                }});
                const result = await response.json();
                
                if (result.success) {{
                    alert(`${{result.message}}`);
                    refreshUsers();  // 刷新用户列表
                }} else {{
                    alert('删除测试用户失败：' + result.message);
                }}
            }} catch (error) {{
                console.error('删除测试用户异常:', error);
                alert('删除测试用户失败：网络错误');
            }}
        }}
        
        async function syncUsers() {{
            const syncBtn = document.querySelector('button[onclick="syncUsers()"]');
            const originalText = syncBtn.innerText;
            syncBtn.innerText = '同步中...';
            syncBtn.disabled = true;
            
            try {{
                const response = await fetch('/api/admin/users/sync', {{ 
                    method: 'POST',
                    credentials: 'include'
                }});
                const result = await response.json();
                if (result.success) {{
                    alert(`同步成功！\\n${{result.message}}`);
                    refreshUsers();
                }} else {{
                    alert('同步失败：' + (result.message || '未知错误'));
                }}
            }} catch (error) {{
                alert('同步失败：网络错误');
            }} finally {{
                syncBtn.innerText = originalText;
                syncBtn.disabled = false;
            }}
        }}
        
        // 页面加载时自动获取用户列表
        document.addEventListener('DOMContentLoaded', function() {{
            refreshUsers();
        }});
        
        async function refreshUsers() {{
            console.log('refreshUsers() 被调用');
            try {{
                console.log('正在请求 /api/admin/users');
                const response = await fetch('/api/admin/users?' + new Date().getTime(), {{
                    credentials: 'include',  // 包含cookie
                    cache: 'no-cache',       // 禁用缓存
                    headers: {{
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }}
                }});
                console.log('响应状态:', response.status);
                if (response.ok) {{
                    const users = await response.json();
                    console.log('获取到用户数据:', users.length, '个用户');
                    displayUsers(users);
                }} else {{
                    console.error('获取用户列表失败:', response.status);
                    const responseText = await response.text();
                    console.error('错误响应内容:', responseText);
                    const tbody = document.querySelector('#usersTable tbody');
                    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 40px;">获取用户列表失败(${{response.status}})，请重新登录</td></tr>`;
                }}
            }} catch (error) {{
                console.error('获取用户列表异常:', error);
                const tbody = document.querySelector('#usersTable tbody');
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px;">网络错误，请刷新页面</td></tr>';
            }}
        }}
        
        function displayUsers(users) {{
            console.log('displayUsers() 被调用，用户数据:', users);
            const tbody = document.querySelector('#usersTable tbody');
            console.log('找到tbody元素:', tbody);
            if (users.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px;">暂无用户数据</td></tr>';
                return;
            }}
            
            // 特别检查张三的数据
            const zhangsan = users.find(user => user.userid === 'zhangsan');
            if (zhangsan) {{
                console.log('张三的数据:', zhangsan);
                console.log('张三的角色:', zhangsan.role, '显示为:', getRoleText(zhangsan.role));
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
                    const response = await fetch(`/api/admin/users/${{userid}}/role`, {{
                        method: 'PUT',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ role: selectedRole }}),
                        credentials: 'include'
                    }});
                    const result = await response.json();
                    if (response.ok) {{
                        console.log('角色修改成功，准备刷新用户列表');
                        alert('角色修改成功');
                        refreshUsers();
                    }} else {{
                        console.error('角色修改失败:', result);
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
                    const response = await fetch(`/api/admin/users/${{userid}}/status`, {{
                        method: 'PUT',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ is_active: !currentStatus }}),
                        credentials: 'include'
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


@router.get("/me")
async def get_admin_info(admin_info: dict = Depends(require_admin_auth)):
    """获取当前管理员信息"""
    return {
        "id": "admin_" + admin_info['username'],
        "userid": admin_info['username'],
        "name": f"管理员-{admin_info['username']}",
        "role": "super_admin"
    }

@router.get("/users")
async def get_users(admin_info: dict = Depends(require_admin_auth), db: Session = Depends(get_db)):
    """获取所有用户列表"""
    try:
        # 强制刷新数据库会话，避免缓存问题
        db.expire_all()  # 清除会话中的所有对象缓存
        
        users = db.query(User).all()
        
        # 如果数据库中只有测试用户，尝试从企业微信同步
        test_userids = {'zhangsan', 'lisi', 'wangwu', 'zhaoliu', 'sunqi'}
        db_userids = {user.userid for user in users}
        
        if test_userids.issubset(db_userids) and len(users) <= 6:
            logger.info("检测到测试用户数据，尝试从企业微信同步真实用户")
            # 自动触发同步
            try:
                wecom = WecomService()
                wecom_users = wecom.get_all_users()
                
                if wecom_users:
                    logger.info(f"从企业微信获取到{len(wecom_users)}个用户，开始同步")
                    # 这里可以触发同步逻辑，但为了简化，先记录日志
                    # 实际同步将通过手动点击同步按钮完成
                else:
                    logger.warning("从企业微信获取用户失败，显示现有数据")
            except Exception as e:
                logger.error(f"尝试同步企业微信用户时出错: {e}")
        
        # 特别检查张三的角色（调试用）
        zhangsan = next((u for u in users if u.userid == 'zhangsan'), None)
        if zhangsan:
            logger.info(f"获取用户列表时，张三的角色为: {zhangsan.role}, 更新时间: {zhangsan.updated_at}")
        
        logger.info(f"成功获取{len(users)}个用户")
        return users
    except Exception as e:
        logger.error(f"获取用户列表异常: {e}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")

@router.post("/users/sync")
async def sync_wecom_users(admin_info: dict = Depends(require_admin_auth), db: Session = Depends(get_db)):
    """同步企业微信用户"""
    try:
        wecom = WecomService()
        
        # 获取企业微信所有用户
        wecom_users = wecom.get_all_users()
        
        # 如果无法从企业微信获取，记录错误并提示用户
        if not wecom_users:
            logger.error("企业微信通讯录权限未开启或corp_secret错误，无法获取用户列表")
            return {
                "success": False,
                "message": "企业微信通讯录权限未开启或凭证配置错误，请在管理后台检查权限/密钥",
                "synced": 0
            }
        
        synced_count = 0
        updated_count = 0
        new_count = 0
        
        for wecom_user in wecom_users:
            userid = wecom_user.get("userid")
            if not userid:
                continue
            
            # 查找本地用户
            local_user = db.query(User).filter(User.userid == userid).first()
            
            if local_user:
                # 更新现有用户信息
                local_user.name = wecom_user.get("name", local_user.name)
                local_user.mobile = wecom_user.get("mobile", local_user.mobile)
                local_user.email = wecom_user.get("email", local_user.email)
                local_user.position = wecom_user.get("position", local_user.position)
                local_user.avatar = wecom_user.get("avatar", local_user.avatar)
                
                # 处理部门信息
                departments = wecom_user.get("department", [])
                if departments:
                    local_user.department = str(departments[0]) if isinstance(departments[0], int) else str(departments)
                
                local_user.updated_at = datetime.now()
                updated_count += 1
            else:
                # 创建新用户
                new_user = User(
                    userid=userid,
                    name=wecom_user.get("name", ""),
                    mobile=wecom_user.get("mobile", ""),
                    email=wecom_user.get("email", ""),
                    position=wecom_user.get("position", ""),
                    avatar=wecom_user.get("avatar", ""),
                    department=str(wecom_user.get("department", [])[0]) if wecom_user.get("department") else "",
                    role="user",  # 默认为普通用户
                    is_active=wecom_user.get("status", 1) == 1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_user)
                new_count += 1
            
            synced_count += 1
        
        # 提交事务
        db.commit()
        
        message = f"同步完成：总计{synced_count}个用户，新增{new_count}个，更新{updated_count}个"
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "total": synced_count,
            "new": new_count,
            "updated": updated_count
        }
        
    except Exception as e:
        logger.error(f"同步企业微信用户失败: {e}")
        db.rollback()
        return {"success": False, "message": f"同步失败: {str(e)}", "synced": 0}

@router.post("/users/cleanup-test")
async def cleanup_test_users(admin_info: dict = Depends(require_admin_auth), db: Session = Depends(get_db)):
    """清理测试用户数据"""
    try:
        wecom = WecomService()
        wecom_users = wecom.get_all_users()

        if not wecom_users:
            logger.error("无法获取企业微信用户，测试用户清理终止")
            return {
                "success": False,
                "message": "无法连接企业微信通讯录，请稍后再试",
                "deleted": 0,
            }

        valid_userids = {user.get("userid") for user in wecom_users if user.get("userid")}

        # 读取保留名单（用于额外的管理员账号）
        keep_userids_env = os.getenv("WECOM_KEEP_USERIDS", "")
        keep_userids = {uid.strip() for uid in keep_userids_env.split(",") if uid.strip()}
        valid_userids.update(keep_userids)

        deleted_users = []

        for user in db.query(User).all():
            if user.userid not in valid_userids:
                deleted_users.append(f"{user.name or '未命名'}({user.userid})")
                db.delete(user)

        deleted_count = len(deleted_users)
        db.commit()

        if deleted_count:
            message = f"成功删除{deleted_count}个测试用户: {', '.join(deleted_users)}"
            logger.info(message)
        else:
            message = "没有找到需要删除的测试用户"

        return {
            "success": True,
            "message": message,
            "deleted": deleted_count,
            "deleted_users": deleted_users
        }

    except Exception as e:
        logger.error(f"删除测试用户失败: {e}")
        db.rollback()
        return {"success": False, "message": f"删除失败: {str(e)}", "deleted": 0}

@router.put("/users/{userid}/role")
async def update_user_role(
    userid: str, 
    role_data: dict,
    admin_info: dict = Depends(require_admin_auth), 
    db: Session = Depends(get_db)
):
    """修改用户角色"""
    try:
        logger.info(f"开始处理角色修改请求: userid={userid}, role_data={role_data}")
        
        user = db.query(User).filter(User.userid == userid).first()
        if not user:
            logger.warning(f"用户不存在: {userid}")
            raise HTTPException(status_code=404, detail="用户不存在")
        
        new_role = role_data.get("role")
        if new_role not in ["user", "manager", "admin", "super_admin"]:
            logger.warning(f"无效的角色: {new_role}")
            raise HTTPException(status_code=400, detail="无效的角色")
        
        # 记录旧角色
        old_role = user.role
        logger.info(f"用户{userid}当前角色: {old_role}, 新角色: {new_role}")
        
        # 更新角色
        user.role = new_role
        user.updated_at = datetime.now()
        
        logger.info("准备提交数据库更改...")
        db.commit()
        logger.info("数据库提交成功")
        
        # 刷新对象以确保数据库状态同步
        db.refresh(user)
        logger.info(f"角色更新后，用户{userid}在数据库中的角色为: {user.role}")
        
        # 如果角色确实发生了变化，记录变更
        if old_role != new_role:
            # 记录角色变更历史
            try:
                record_role_change(userid, old_role, new_role)
                logger.info("角色变更历史记录成功")
            except Exception as e:
                logger.warning(f"记录角色变更历史失败: {e}")
            
            logger.info(f"用户{userid}角色从{old_role}修改为{new_role}，立即生效")
            
            return {
                "success": True, 
                "message": f"角色修改成功，新权限立即生效",
                "role_changed": True,
                "old_role": old_role,
                "new_role": new_role
            }
        else:
            return {"success": True, "message": "角色未发生变化"}
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.exception(f"角色修改过程中发生异常: {e}")
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改失败: {str(e)}")

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
