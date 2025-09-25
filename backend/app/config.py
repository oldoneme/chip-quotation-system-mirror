"""
应用配置文件
包含企业微信和其他系统配置
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional, List


def get_environment() -> str:
    """获取当前环境"""
    return os.getenv("ENVIRONMENT", "development").lower()


def get_default_frontend_url() -> str:
    """根据环境获取前端默认URL"""
    env = get_environment()
    if env == "production":
        return "https://wecom.chipinfos.com.cn"
    elif env == "staging":
        return "https://wecom-staging.chipinfos.com.cn"
    return "https://wecom-dev.chipinfos.com.cn"  # 开发环境（隧道）


def get_default_api_url() -> str:
    """根据环境获取API默认URL"""
    env = get_environment()
    if env == "production":
        return "https://api.chipinfos.com.cn"
    elif env == "staging":
        return "https://api-staging.chipinfos.com.cn"
    return "https://wecom-dev.chipinfos.com.cn/api"  # 开发环境（隧道路径代理）


def get_cors_origins() -> List[str]:
    """根据环境获取CORS配置"""
    # 优先使用环境变量
    origins_env = os.getenv("CORS_ORIGINS", "")
    if origins_env:
        return [origin.strip() for origin in origins_env.split(",") if origin.strip()]
    
    # 根据环境返回默认值
    env = get_environment()
    if env == "production":
        return [
            "https://wecom.chipinfos.com.cn",
            "https://app.chipinfos.com.cn"
        ]
    elif env == "staging":
        return [
            "https://wecom-staging.chipinfos.com.cn",
            "https://app-staging.chipinfos.com.cn"
        ]
    
    # 开发环境默认值
    return [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]


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
    WECOM_CALLBACK_TOKEN: str = os.getenv("WECOM_CALLBACK_TOKEN", "cN9bXxcD80")
    WECOM_ENCODING_AES_KEY: str = os.getenv("WECOM_ENCODING_AES_KEY", "S1iZ8DxsKGpiL3b10oVpRm59FphYwKzhtdSCR18q3nl")
    WECOM_APPROVAL_TEMPLATE_ID: str = os.getenv("WECOM_APPROVAL_TEMPLATE_ID", "")
    
    # 回调URL配置 - 使用环境感知默认值
    WECOM_CALLBACK_URL: str = os.getenv("WECOM_CALLBACK_URL", get_default_frontend_url())
    WECOM_BASE_URL: str = os.getenv("WECOM_BASE_URL", get_default_frontend_url())
    API_BASE_URL: str = os.getenv("API_BASE_URL", get_default_api_url())
    WECOM_CORP_SECRET: str = os.getenv("WECOM_CORP_SECRET", "")
    
    # 前端基础URL（用于审批链接）
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", get_default_frontend_url())
    SNAPSHOT_BROWSER_POOL: int = int(os.getenv("SNAPSHOT_BROWSER_POOL", "2"))
    SNAPSHOT_READY_SELECTOR: str = os.getenv("SNAPSHOT_READY_SELECTOR", "#quote-ready")
    
    # 审批链接配置
    APPROVAL_LINK_EXPIRE_DAYS: int = 7  # 审批链接有效期（天）
    
    # CORS配置 - 使用环境感知配置
    CORS_ORIGINS: List[str] = get_cors_origins()
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 允许额外字段，防止现有环境变量导致错误


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
