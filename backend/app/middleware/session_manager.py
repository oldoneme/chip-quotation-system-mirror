"""
会话管理模块
处理用户角色变更时的会话刷新
"""
import redis
import json
import logging
from typing import Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        """初始化会话管理器"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=1
            )
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Redis连接成功，使用Redis管理会话")
        except:
            self.use_redis = False
            self._memory_cache = {}
            logger.warning("Redis连接失败，使用内存管理会话")
    
    def invalidate_user_sessions(self, userid: str) -> bool:
        """
        使用户的所有会话失效
        
        Args:
            userid: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            if self.use_redis:
                # 在Redis中标记用户会话失效
                key = f"user_session_invalidated:{userid}"
                self.redis_client.setex(key, 3600, datetime.now().isoformat())  # 1小时过期
                logger.info(f"用户{userid}的会话已在Redis中标记为失效")
            else:
                # 内存中标记会话失效
                key = f"user_session_invalidated:{userid}"
                self._memory_cache[key] = {
                    'invalidated_at': datetime.now(),
                    'expires_at': datetime.now() + timedelta(hours=1)
                }
                logger.info(f"用户{userid}的会话已在内存中标记为失效")
            
            return True
        except Exception as e:
            logger.error(f"标记用户{userid}会话失效时出错: {e}")
            return False
    
    def is_session_invalidated(self, userid: str, login_time: datetime) -> bool:
        """
        检查用户会话是否已失效
        
        Args:
            userid: 用户ID
            login_time: 用户登录时间
            
        Returns:
            bool: 会话是否已失效
        """
        try:
            if self.use_redis:
                key = f"user_session_invalidated:{userid}"
                invalidated_time_str = self.redis_client.get(key)
                if invalidated_time_str:
                    invalidated_time = datetime.fromisoformat(invalidated_time_str)
                    # 如果失效时间晚于登录时间，则会话已失效
                    return invalidated_time > login_time
            else:
                key = f"user_session_invalidated:{userid}"
                cached = self._memory_cache.get(key)
                if cached and cached['expires_at'] > datetime.now():
                    invalidated_time = cached['invalidated_at']
                    return invalidated_time > login_time
            
            return False
        except Exception as e:
            logger.error(f"检查用户{userid}会话失效状态时出错: {e}")
            return False
    
    def record_role_change(self, userid: str, old_role: str, new_role: str) -> bool:
        """
        记录角色变更
        
        Args:
            userid: 用户ID
            old_role: 旧角色
            new_role: 新角色
            
        Returns:
            bool: 是否成功
        """
        try:
            change_record = {
                'userid': userid,
                'old_role': old_role,
                'new_role': new_role,
                'changed_at': datetime.now().isoformat(),
                'requires_relogin': True
            }
            
            if self.use_redis:
                key = f"role_change:{userid}:{int(datetime.now().timestamp())}"
                self.redis_client.setex(key, 86400, json.dumps(change_record))  # 24小时
            else:
                key = f"role_change:{userid}"
                self._memory_cache[key] = change_record
            
            logger.info(f"记录用户{userid}角色变更: {old_role} -> {new_role}")
            return True
        except Exception as e:
            logger.error(f"记录角色变更时出错: {e}")
            return False
    
    def get_user_role_changes(self, userid: str, since: datetime) -> list:
        """
        获取用户的角色变更记录
        
        Args:
            userid: 用户ID
            since: 开始时间
            
        Returns:
            list: 角色变更记录列表
        """
        changes = []
        try:
            if self.use_redis:
                # 扫描Redis中的角色变更记录
                pattern = f"role_change:{userid}:*"
                keys = self.redis_client.keys(pattern)
                for key in keys:
                    record_str = self.redis_client.get(key)
                    if record_str:
                        record = json.loads(record_str)
                        changed_at = datetime.fromisoformat(record['changed_at'])
                        if changed_at > since:
                            changes.append(record)
            else:
                # 从内存中获取记录
                key = f"role_change:{userid}"
                record = self._memory_cache.get(key)
                if record:
                    changed_at = datetime.fromisoformat(record['changed_at'])
                    if changed_at > since:
                        changes.append(record)
        except Exception as e:
            logger.error(f"获取用户{userid}角色变更记录时出错: {e}")
        
        return sorted(changes, key=lambda x: x['changed_at'], reverse=True)

# 全局会话管理器实例
session_manager = SessionManager()

def invalidate_user_sessions(userid: str) -> bool:
    """使用户会话失效的便捷函数"""
    return session_manager.invalidate_user_sessions(userid)

def is_session_invalidated(userid: str, login_time: datetime) -> bool:
    """检查会话是否失效的便捷函数"""
    return session_manager.is_session_invalidated(userid, login_time)

def record_role_change(userid: str, old_role: str, new_role: str) -> bool:
    """记录角色变更的便捷函数"""
    return session_manager.record_role_change(userid, old_role, new_role)