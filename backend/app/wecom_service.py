"""
企业微信API服务模块
提供获取access_token、用户列表、部门列表等功能
"""
import os
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import redis
import json

logger = logging.getLogger(__name__)

class WecomService:
    """企业微信服务类"""
    
    def __init__(self):
        self.corp_id = os.getenv("WECOM_CORP_ID")
        self.corp_secret = os.getenv("WECOM_CORP_SECRET")
        self.agent_id = os.getenv("WECOM_AGENT_ID")
        self.base_url = "https://qyapi.weixin.qq.com/cgi-bin"
        
        # Redis客户端用于缓存token
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=1
            )
            self.redis_client.ping()
            self.use_redis = True
        except:
            logger.warning("Redis连接失败，将使用内存缓存")
            self.use_redis = False
            self._token_cache = {}
    
    def get_access_token(self) -> Optional[str]:
        """
        获取企业微信access_token
        优先从缓存获取，过期后重新请求
        """
        cache_key = f"wecom_access_token_{self.corp_id}"
        
        # 尝试从缓存获取
        if self.use_redis:
            token = self.redis_client.get(cache_key)
            if token:
                return token
        else:
            cached = self._token_cache.get(cache_key)
            if cached and cached['expires_at'] > datetime.now():
                return cached['token']
        
        # 请求新token
        url = f"{self.base_url}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                token = data.get("access_token")
                expires_in = data.get("expires_in", 7200)
                
                # 缓存token（提前5分钟过期）
                if self.use_redis:
                    self.redis_client.setex(
                        cache_key,
                        expires_in - 300,
                        token
                    )
                else:
                    self._token_cache[cache_key] = {
                        'token': token,
                        'expires_at': datetime.now() + timedelta(seconds=expires_in - 300)
                    }
                
                logger.info("成功获取企业微信access_token")
                return token
            else:
                logger.error(f"获取access_token失败: {data}")
                return None
                
        except Exception as e:
            logger.error(f"请求access_token异常: {e}")
            return None
    
    def get_department_list(self) -> List[Dict]:
        """
        获取部门列表
        """
        token = self.get_access_token()
        if not token:
            return []
        
        url = f"{self.base_url}/department/list"
        params = {"access_token": token}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                return data.get("department", [])
            else:
                logger.error(f"获取部门列表失败: {data}")
                return []
                
        except Exception as e:
            logger.error(f"请求部门列表异常: {e}")
            return []
    
    def get_department_users(self, department_id: int = 1, fetch_child: bool = True) -> List[Dict]:
        """
        获取部门成员列表
        
        Args:
            department_id: 部门ID，默认为1（根部门）
            fetch_child: 是否递归获取子部门成员
        """
        token = self.get_access_token()
        if not token:
            return []
        
        url = f"{self.base_url}/user/simplelist"
        params = {
            "access_token": token,
            "department_id": department_id,
            "fetch_child": 1 if fetch_child else 0
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                return data.get("userlist", [])
            else:
                logger.error(f"获取部门成员失败: {data}")
                return []
                
        except Exception as e:
            logger.error(f"请求部门成员异常: {e}")
            return []
    
    def get_user_detail(self, userid: str) -> Optional[Dict]:
        """
        获取用户详细信息
        
        Args:
            userid: 企业微信用户ID
        """
        token = self.get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/user/get"
        params = {
            "access_token": token,
            "userid": userid
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                return data
            else:
                logger.error(f"获取用户详情失败: {data}")
                return None
                
        except Exception as e:
            logger.error(f"请求用户详情异常: {e}")
            return None
    
    def batch_get_users(self, userids: List[str]) -> List[Dict]:
        """
        批量获取用户详细信息
        
        Args:
            userids: 用户ID列表
        """
        users = []
        for userid in userids:
            user = self.get_user_detail(userid)
            if user:
                users.append(user)
        return users
    
    def get_all_users(self) -> List[Dict]:
        """
        获取应用可见范围内的所有用户
        使用应用接口而不是通讯录接口
        """
        token = self.get_access_token()
        if not token:
            return []
        
        # 使用agent/get_workbench_template接口获取应用可见用户
        # 或者使用message/send接口的touser参数@all获取用户列表
        # 但最直接的方式是通过已登录的用户获取
        
        # 尝试使用应用权限获取用户
        try:
            # 由于没有通讯录权限，我们暂时返回空列表
            # 实际使用时，应该从已登录用户中获取
            logger.warning("当前应用没有通讯录权限，请在企业微信管理后台开启")
            return []
            
        except Exception as e:
            logger.error(f"获取用户列表异常: {e}")
            return []
    
    def get_visible_users(self) -> List[Dict]:
        """
        获取应用可见范围内的用户
        只返回简单信息，性能更好
        """
        return self.get_department_users(department_id=1, fetch_child=True)