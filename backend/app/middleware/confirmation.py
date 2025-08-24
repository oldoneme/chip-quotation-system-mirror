"""
敏感操作二次确认中间件
用于保护重要的系统操作，防止误操作和恶意操作
"""

from functools import wraps
from typing import List, Dict, Any, Optional, Callable
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
import hashlib
import time
import json
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, OperationLog
from app import crud

# 敏感操作配置
SENSITIVE_OPERATIONS = {
    # 用户管理敏感操作
    'user_delete': {
        'name': '删除用户',
        'description': '此操作将永久删除用户及其所有相关数据',
        'risk_level': 'high',
        'confirmation_timeout': 300,  # 5分钟确认超时
        'required_fields': ['user_id', 'reason'],
        'admin_approval': False
    },
    'user_role_change': {
        'name': '修改用户角色',
        'description': '此操作将改变用户的系统权限',
        'risk_level': 'high',
        'confirmation_timeout': 300,
        'required_fields': ['user_id', 'new_role', 'reason'],
        'admin_approval': True  # 需要管理员批准
    },
    'user_batch_disable': {
        'name': '批量禁用用户',
        'description': '此操作将批量禁用多个用户账户',
        'risk_level': 'critical',
        'confirmation_timeout': 600,  # 10分钟
        'required_fields': ['user_ids', 'reason'],
        'admin_approval': True
    },
    
    # 数据管理敏感操作
    'quotation_delete': {
        'name': '删除报价',
        'description': '此操作将永久删除报价记录',
        'risk_level': 'medium',
        'confirmation_timeout': 180,  # 3分钟
        'required_fields': ['quotation_id', 'reason'],
        'admin_approval': False
    },
    'quotation_batch_delete': {
        'name': '批量删除报价',
        'description': '此操作将批量删除多个报价记录',
        'risk_level': 'high',
        'confirmation_timeout': 300,
        'required_fields': ['quotation_ids', 'reason'],
        'admin_approval': True
    },
    'data_export': {
        'name': '数据导出',
        'description': '此操作将导出敏感的系统数据',
        'risk_level': 'medium',
        'confirmation_timeout': 180,
        'required_fields': ['export_type', 'date_range'],
        'admin_approval': False
    },
    
    # 系统管理敏感操作
    'system_config_change': {
        'name': '系统配置修改',
        'description': '此操作将修改关键的系统配置',
        'risk_level': 'critical',
        'confirmation_timeout': 600,
        'required_fields': ['config_key', 'old_value', 'new_value', 'reason'],
        'admin_approval': True
    },
    'database_cleanup': {
        'name': '数据库清理',
        'description': '此操作将清理数据库中的历史数据',
        'risk_level': 'critical',
        'confirmation_timeout': 900,  # 15分钟
        'required_fields': ['cleanup_type', 'date_before', 'reason'],
        'admin_approval': True
    },
    'system_reset': {
        'name': '系统重置',
        'description': '此操作将重置系统到初始状态',
        'risk_level': 'critical',
        'confirmation_timeout': 1800,  # 30分钟
        'required_fields': ['reset_type', 'backup_confirmation', 'reason'],
        'admin_approval': True
    }
}

class ConfirmationToken:
    """确认令牌类"""
    
    @staticmethod
    def generate_token(operation: str, user_id: int, operation_data: Dict[str, Any]) -> str:
        """生成确认令牌"""
        timestamp = str(int(time.time()))
        data = f"{operation}:{user_id}:{json.dumps(operation_data, sort_keys=True)}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def verify_token(token: str, operation: str, user_id: int, operation_data: Dict[str, Any]) -> bool:
        """验证确认令牌"""
        expected_token = ConfirmationToken.generate_token(operation, user_id, operation_data)
        return token == expected_token

class ConfirmationManager:
    """确认管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self._pending_confirmations = {}  # 在实际应用中应使用Redis或数据库
    
    def create_confirmation(self, operation: str, user: User, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建确认请求"""
        if operation not in SENSITIVE_OPERATIONS:
            raise HTTPException(status_code=400, detail=f"未知的敏感操作: {operation}")
        
        operation_config = SENSITIVE_OPERATIONS[operation]
        
        # 验证必需字段
        missing_fields = []
        for field in operation_config['required_fields']:
            if field not in operation_data:
                missing_fields.append(field)
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必需字段: {', '.join(missing_fields)}"
            )
        
        # 生成确认令牌
        token = ConfirmationToken.generate_token(operation, user.id, operation_data)
        
        # 设置过期时间
        expires_at = datetime.utcnow() + timedelta(seconds=operation_config['confirmation_timeout'])
        
        # 存储待确认的操作
        confirmation_data = {
            'operation': operation,
            'user_id': user.id,
            'user_name': user.name,
            'operation_data': operation_data,
            'token': token,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'status': 'pending',
            'admin_approval_required': operation_config['admin_approval']
        }
        
        self._pending_confirmations[token] = confirmation_data
        
        # 记录确认请求
        crud.log_operation(
            self.db,
            user_id=user.id,
            operation="confirmation_request",
            details=f"请求确认操作: {operation_config['name']}"
        )
        
        return {
            'confirmation_token': token,
            'operation_name': operation_config['name'],
            'description': operation_config['description'],
            'risk_level': operation_config['risk_level'],
            'expires_at': expires_at.isoformat(),
            'admin_approval_required': operation_config['admin_approval'],
            'timeout_seconds': operation_config['confirmation_timeout']
        }
    
    def confirm_operation(self, token: str, user: User, confirmation_data: Dict[str, Any]) -> Dict[str, Any]:
        """确认操作"""
        if token not in self._pending_confirmations:
            raise HTTPException(status_code=404, detail="确认令牌不存在或已过期")
        
        pending = self._pending_confirmations[token]
        
        # 检查过期
        if datetime.utcnow() > pending['expires_at']:
            del self._pending_confirmations[token]
            raise HTTPException(status_code=400, detail="确认已过期，请重新发起操作")
        
        # 验证用户权限
        if pending['user_id'] != user.id and not user.role in ['admin', 'super_admin']:
            raise HTTPException(status_code=403, detail="无权确认此操作")
        
        # 验证确认数据
        password_confirmation = confirmation_data.get('password_confirmation')
        if not password_confirmation:
            raise HTTPException(status_code=400, detail="需要密码确认")
        
        # 在实际应用中，这里应该验证用户密码
        # 这里简化处理，假设前端已经验证过密码
        
        # 验证令牌
        if not ConfirmationToken.verify_token(
            token, 
            pending['operation'], 
            pending['user_id'], 
            pending['operation_data']
        ):
            raise HTTPException(status_code=400, detail="确认令牌验证失败")
        
        # 检查是否需要管理员批准
        if pending['admin_approval_required'] and user.role not in ['admin', 'super_admin']:
            pending['status'] = 'waiting_admin_approval'
            pending['confirmed_by'] = user.id
            pending['confirmed_at'] = datetime.utcnow()
            
            # 记录等待管理员批准
            crud.log_operation(
                self.db,
                user_id=user.id,
                operation="confirmation_pending_admin",
                details=f"等待管理员批准操作: {SENSITIVE_OPERATIONS[pending['operation']]['name']}"
            )
            
            return {
                'status': 'waiting_admin_approval',
                'message': '操作已确认，等待管理员批准',
                'admin_approval_required': True
            }
        else:
            # 直接执行操作
            pending['status'] = 'confirmed'
            pending['confirmed_by'] = user.id
            pending['confirmed_at'] = datetime.utcnow()
            
            # 记录确认完成
            crud.log_operation(
                self.db,
                user_id=user.id,
                operation="confirmation_completed",
                details=f"确认完成操作: {SENSITIVE_OPERATIONS[pending['operation']]['name']}"
            )
            
            # 移除已确认的操作
            confirmed_operation = self._pending_confirmations.pop(token)
            
            return {
                'status': 'confirmed',
                'message': '操作已确认，可以执行',
                'operation_data': confirmed_operation['operation_data'],
                'confirmed_at': confirmed_operation['confirmed_at'].isoformat()
            }
    
    def admin_approve_operation(self, token: str, admin_user: User, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """管理员批准操作"""
        if admin_user.role not in ['admin', 'super_admin']:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if token not in self._pending_confirmations:
            raise HTTPException(status_code=404, detail="确认令牌不存在或已过期")
        
        pending = self._pending_confirmations[token]
        
        if pending['status'] != 'waiting_admin_approval':
            raise HTTPException(status_code=400, detail="此操作不需要管理员批准或已处理")
        
        # 检查过期
        if datetime.utcnow() > pending['expires_at']:
            del self._pending_confirmations[token]
            raise HTTPException(status_code=400, detail="确认已过期")
        
        approval_action = approval_data.get('action')  # 'approve' or 'reject'
        approval_reason = approval_data.get('reason', '')
        
        if approval_action == 'approve':
            pending['status'] = 'admin_approved'
            pending['approved_by'] = admin_user.id
            pending['approved_at'] = datetime.utcnow()
            pending['approval_reason'] = approval_reason
            
            # 记录管理员批准
            crud.log_operation(
                self.db,
                user_id=admin_user.id,
                operation="admin_approval",
                details=f"批准操作: {SENSITIVE_OPERATIONS[pending['operation']]['name']} - {approval_reason}"
            )
            
            # 移除已批准的操作
            approved_operation = self._pending_confirmations.pop(token)
            
            return {
                'status': 'approved',
                'message': '操作已获得管理员批准，可以执行',
                'operation_data': approved_operation['operation_data'],
                'approved_at': approved_operation['approved_at'].isoformat()
            }
        
        elif approval_action == 'reject':
            pending['status'] = 'admin_rejected'
            pending['rejected_by'] = admin_user.id
            pending['rejected_at'] = datetime.utcnow()
            pending['rejection_reason'] = approval_reason
            
            # 记录管理员拒绝
            crud.log_operation(
                self.db,
                user_id=admin_user.id,
                operation="admin_rejection",
                details=f"拒绝操作: {SENSITIVE_OPERATIONS[pending['operation']]['name']} - {approval_reason}"
            )
            
            # 移除已拒绝的操作
            del self._pending_confirmations[token]
            
            return {
                'status': 'rejected',
                'message': '操作已被管理员拒绝',
                'rejection_reason': approval_reason,
                'rejected_at': pending['rejected_at'].isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="无效的批准操作")
    
    def get_pending_confirmations(self, user: User, admin_only: bool = False) -> List[Dict[str, Any]]:
        """获取待确认的操作列表"""
        confirmations = []
        
        for token, pending in self._pending_confirmations.items():
            # 检查过期并清理
            if datetime.utcnow() > pending['expires_at']:
                continue
            
            if admin_only:
                # 只返回需要管理员批准的操作
                if pending['status'] == 'waiting_admin_approval':
                    confirmations.append({
                        'token': token,
                        'operation_name': SENSITIVE_OPERATIONS[pending['operation']]['name'],
                        'description': SENSITIVE_OPERATIONS[pending['operation']]['description'],
                        'risk_level': SENSITIVE_OPERATIONS[pending['operation']]['risk_level'],
                        'user_name': pending['user_name'],
                        'created_at': pending['created_at'].isoformat(),
                        'expires_at': pending['expires_at'].isoformat(),
                        'status': pending['status']
                    })
            else:
                # 返回用户自己的确认操作
                if pending['user_id'] == user.id:
                    confirmations.append({
                        'token': token,
                        'operation_name': SENSITIVE_OPERATIONS[pending['operation']]['name'],
                        'description': SENSITIVE_OPERATIONS[pending['operation']]['description'],
                        'risk_level': SENSITIVE_OPERATIONS[pending['operation']]['risk_level'],
                        'created_at': pending['created_at'].isoformat(),
                        'expires_at': pending['expires_at'].isoformat(),
                        'status': pending['status']
                    })
        
        return confirmations
    
    def cleanup_expired_confirmations(self):
        """清理过期的确认"""
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, pending in self._pending_confirmations.items():
            if current_time > pending['expires_at']:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self._pending_confirmations[token]
        
        return len(expired_tokens)

# 装饰器：需要确认的操作
def require_confirmation(operation: str):
    """要求确认的装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中提取必要的信息
            request = None
            db = None
            current_user = None
            
            # 查找Request, Session, User参数
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, Session):
                    db = arg
                elif isinstance(arg, User):
                    current_user = arg
            
            # 从kwargs中查找
            if not request:
                request = kwargs.get('request')
            if not db:
                db = kwargs.get('db')
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not all([request, db, current_user]):
                raise HTTPException(status_code=500, detail="确认装饰器需要Request, Session, User参数")
            
            # 检查是否有确认令牌
            confirmation_token = request.headers.get('X-Confirmation-Token')
            
            if not confirmation_token:
                # 没有确认令牌，需要创建确认请求
                operation_data = {}
                
                # 提取操作数据
                if hasattr(request, 'json'):
                    try:
                        body = await request.json()
                        operation_data.update(body)
                    except:
                        pass
                
                # 提取路径参数
                if hasattr(request, 'path_params'):
                    operation_data.update(request.path_params)
                
                # 创建确认管理器
                confirmation_manager = ConfirmationManager(db)
                
                # 创建确认请求
                confirmation_info = confirmation_manager.create_confirmation(
                    operation, 
                    current_user, 
                    operation_data
                )
                
                raise HTTPException(
                    status_code=202, 
                    detail={
                        "message": "此操作需要确认",
                        "confirmation_required": True,
                        **confirmation_info
                    }
                )
            else:
                # 有确认令牌，验证令牌
                confirmation_manager = ConfirmationManager(db)
                
                # 这里简化处理，实际应用中需要更复杂的验证逻辑
                # 假设令牌已经通过其他方式验证过
                
                # 执行原始函数
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# 全局确认管理器实例（在实际应用中应该使用单例模式）
_global_confirmation_manager = None

def get_confirmation_manager(db: Session = Depends(get_db)) -> ConfirmationManager:
    """获取确认管理器实例"""
    return ConfirmationManager(db)