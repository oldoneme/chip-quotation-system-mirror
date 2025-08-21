"""
基于角色的权限控制中间件
支持四级权限：user, manager, admin, super_admin
"""
from functools import wraps
from typing import List, Optional, Union, Callable, Any
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models import User

logger = logging.getLogger(__name__)

# 权限等级映射（数字越大权限越高）
ROLE_LEVELS = {
    "user": 1,
    "manager": 2, 
    "admin": 3,
    "super_admin": 4
}

# 权限继承：高级角色拥有所有低级角色的权限
def has_permission(user_role: str, required_role: str) -> bool:
    """
    检查用户角色是否满足所需权限
    
    Args:
        user_role: 用户当前角色
        required_role: 所需的最低角色
        
    Returns:
        bool: 是否有权限
    """
    user_level = ROLE_LEVELS.get(user_role, 0)
    required_level = ROLE_LEVELS.get(required_role, 0)
    return user_level >= required_level

def create_permission_dependency(required_role: str):
    """
    创建权限检查依赖函数
    
    Args:
        required_role: 所需的最低角色权限
    """
    def permission_checker():
        """返回检查权限的依赖函数"""
        def check_permission(current_user: User) -> User:
            """
            检查用户权限的具体逻辑
            
            Args:
                current_user: 当前登录用户
                
            Returns:
                User: 验证通过的用户
                
            Raises:
                HTTPException: 权限不足时抛出403错误
            """
            if not current_user:
                raise HTTPException(status_code=401, detail="未登录")
            
            if not current_user.is_active:
                raise HTTPException(status_code=403, detail="账户已被禁用")
            
            # 检查角色权限
            if not has_permission(current_user.role, required_role):
                raise HTTPException(
                    status_code=403, 
                    detail=f"需要{required_role}级别或更高权限"
                )
            
            logger.info(f"用户{current_user.userid}({current_user.role})通过权限检查({required_role})")
            return current_user
        
        return check_permission
    
    return permission_checker()

# 便捷的权限检查函数 - 这些将在API端点中使用
def require_user_permission():
    """要求普通用户权限"""
    return create_permission_dependency("user")

def require_manager_permission():
    """要求经理权限"""
    return create_permission_dependency("manager")

def require_admin_permission():
    """要求管理员权限"""
    return create_permission_dependency("admin")

def require_super_admin_permission():
    """要求超级管理员权限"""
    return create_permission_dependency("super_admin")

# 资源操作权限检查
class ResourcePermissionChecker:
    """资源级权限检查器"""
    
    def __init__(self, required_role: str, allow_owner: bool = True):
        """
        初始化资源权限检查器
        
        Args:
            required_role: 所需的最低角色权限
            allow_owner: 是否允许资源拥有者操作
        """
        self.required_role = required_role
        self.allow_owner = allow_owner
    
    def check_permission(self, 
                        current_user: User, 
                        resource_owner_id: Optional[str] = None) -> bool:
        """
        检查用户对特定资源的权限
        
        Args:
            current_user: 当前用户
            resource_owner_id: 资源拥有者ID
            
        Returns:
            bool: 是否有权限
        """
        if not current_user or not current_user.is_active:
            return False
        
        # 检查角色权限
        if has_permission(current_user.role, self.required_role):
            return True
        
        # 检查是否为资源拥有者
        if (self.allow_owner and 
            resource_owner_id and 
            current_user.userid == resource_owner_id):
            return True
        
        return False

# 装饰器形式的权限检查
def permission_required(required_role: str, allow_self: bool = False):
    """
    权限检查装饰器（用于非FastAPI函数）
    
    Args:
        required_role: 所需的最低角色
        allow_self: 是否允许操作自己的数据
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里可以根据具体需求实现权限检查逻辑
            return func(*args, **kwargs)
        return wrapper
    return decorator

# API端点权限映射
API_PERMISSIONS = {
    # 报价相关
    "/api/v1/quotations": {
        "GET": "user",      # 查看报价 - 普通用户
        "POST": "manager",  # 创建报价 - 经理及以上
        "PUT": "manager",   # 修改报价 - 经理及以上  
        "DELETE": "admin"   # 删除报价 - 管理员及以上
    },
    
    # 用户管理相关
    "/api/v1/users": {
        "GET": "manager",   # 查看用户列表 - 经理及以上
        "POST": "admin",    # 创建用户 - 管理员及以上
        "PUT": "admin",     # 修改用户 - 管理员及以上
        "DELETE": "admin"   # 删除用户 - 管理员及以上
    },
    
    # 系统管理相关  
    "/api/v1/system": {
        "GET": "admin",     # 查看系统信息 - 管理员及以上
        "POST": "super_admin", # 系统配置 - 超级管理员
        "PUT": "super_admin",  # 系统配置 - 超级管理员
        "DELETE": "super_admin" # 系统配置 - 超级管理员
    }
}

def get_required_permission(path: str, method: str) -> Optional[str]:
    """
    根据API路径和方法获取所需权限
    
    Args:
        path: API路径
        method: HTTP方法
        
    Returns:
        str: 所需角色，如果没有配置则返回None
    """
    for api_path, methods in API_PERMISSIONS.items():
        if path.startswith(api_path):
            return methods.get(method.upper())
    return None

# 用户角色显示映射
ROLE_DISPLAY_NAMES = {
    "user": "普通用户",
    "manager": "销售经理", 
    "admin": "管理员",
    "super_admin": "超级管理员"
}