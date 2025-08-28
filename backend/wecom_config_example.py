#!/usr/bin/env python3
"""
企业微信审批配置示例文件
请复制此文件为 wecom_config.py 并填入真实配置
"""

# 企业微信配置
WECOM_CORP_ID = "your_corp_id_here"  # 企业ID
WECOM_AGENT_ID = "your_agent_id_here"  # 应用ID  
WECOM_CORP_SECRET = "your_corp_secret_here"  # 应用Secret

# 审批模板ID（需要在企业微信管理后台创建审批模板）
WECOM_QUOTE_TEMPLATE_ID = "your_template_id_here"

# 默认审批人配置
DEFAULT_APPROVERS = [
    "admin",  # 企业微信用户ID
    # 可以添加更多审批人
]

# 审批流程配置
APPROVAL_CONFIG = {
    # 是否启用企业微信审批
    "enabled": False,
    
    # 审批超时时间（小时）
    "timeout_hours": 24,
    
    # 自动提醒配置
    "reminder": {
        "enabled": True,
        "interval_hours": 4  # 每4小时提醒一次
    }
}