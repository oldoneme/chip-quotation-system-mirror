"""
应用配置文件
包含企业微信和其他系统配置
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "芯片测试报价系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./app/test.db"
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # DeepLink JWT配置
    DEEPLINK_JWT_SECRET: str = os.getenv("DEEPLINK_JWT_SECRET", "your-deeplink-secret-change-in-production")
    DEEPLINK_JWT_TTL_SECONDS: int = int(os.getenv("DEEPLINK_JWT_TTL_SECONDS", "900"))
    
    # 企业微信配置
    WECOM_CORP_ID: str = os.getenv("WECOM_CORP_ID", "")
    WECOM_AGENT_ID: int = int(os.getenv("WECOM_AGENT_ID", "0"))
    WECOM_SECRET: str = os.getenv("WECOM_SECRET", "")
    WECOM_CALLBACK_TOKEN: str = os.getenv("WECOM_CALLBACK_TOKEN", "")
    WECOM_ENCODING_AES_KEY: str = os.getenv("WECOM_ENCODING_AES_KEY", "")
    WECOM_APPROVAL_TEMPLATE_ID: str = os.getenv("WECOM_APPROVAL_TEMPLATE_ID", "")
    
    # 回调URL配置
    WECOM_CALLBACK_URL: str = os.getenv("WECOM_CALLBACK_URL", "http://localhost:3000")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # 审批链接配置
    APPROVAL_LINK_EXPIRE_DAYS: int = 7  # 审批链接有效期（天）
    
    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 允许额外字段，防止现有环境变量导致错误


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings