"""
应用配置管理
"""
from typing import List
from dataclasses import dataclass, field


@dataclass
class Settings:
    """应用配置"""
    
    # 基本配置
    APP_NAME: str = "芯片测试报价系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./app/test.db"
    DATABASE_ECHO: bool = False
    
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Chip Quotation System"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"])
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 业务配置
    ENGINEER_HOURLY_RATE: float = 350.0
    TECHNICIAN_HOURLY_RATE: float = 200.0
    DEFAULT_ENGINEERING_RATE: float = 1.2
    DEFAULT_EXCHANGE_RATE_USD: float = 7.0
    MIN_DISCOUNT_RATE: float = 0.1
    MAX_DISCOUNT_RATE: float = 2.0
    
    # 缓存配置
    CACHE_TTL: int = 300  # 5分钟


# 导出配置实例
settings = Settings()