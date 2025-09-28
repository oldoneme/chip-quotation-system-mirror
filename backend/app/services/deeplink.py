import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ..config import settings

class DeepLinkService:
    """深链接JWT服务"""
    
    def __init__(self):
        self.secret = settings.DEEPLINK_JWT_SECRET
        self.ttl_seconds = getattr(settings, 'DEEPLINK_JWT_TTL_SECONDS', 900)  # 15分钟
        self.algorithm = 'HS256'
    
    def make_token(self, quote_id: int, snapshot_id: int, ttl: int = None) -> str:
        """生成短效JWT token"""
        if ttl is None:
            ttl = self.ttl_seconds
            
        payload = {
            'quote_id': quote_id,
            'snapshot_id': snapshot_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=ttl),
            'purpose': 'deeplink_access'
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证token并返回payload"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            
            # 验证purpose字段
            if payload.get('purpose') != 'deeplink_access':
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token过期
        except jwt.InvalidTokenError:
            return None  # Token无效
    
    def build_deeplink(self, quote_id: int, snapshot_id: int) -> str:
        """构建前端深链接"""
        token = self.make_token(quote_id, snapshot_id)
        base_url = settings.WECOM_BASE_URL.rstrip('/')
        return f"{base_url}/quote/{quote_id}?snap={snapshot_id}&t={token}"

# 全局实例
deeplink_service = DeepLinkService()
