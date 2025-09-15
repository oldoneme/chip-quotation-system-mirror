"""
管理员API模块
提供管理员专用的高权限接口
"""

from .quotes import router as quotes_router
from .permissions import require_admin_role, require_super_admin_role

__all__ = ["quotes_router", "require_admin_role", "require_super_admin_role"]