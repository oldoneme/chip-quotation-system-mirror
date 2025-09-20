#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

def test_environment_variables():
    """测试环境变量加载"""
    print("🔧 测试环境变量加载")
    print("=" * 50)

    # 检查关键的企业微信环境变量
    wecom_vars = {
        "WECOM_CORP_ID": os.getenv("WECOM_CORP_ID"),
        "WECOM_AGENT_ID": os.getenv("WECOM_AGENT_ID"),
        "WECOM_SECRET": os.getenv("WECOM_SECRET"),
        "WECOM_APPROVAL_TEMPLATE_ID": os.getenv("WECOM_APPROVAL_TEMPLATE_ID"),
    }

    for var_name, var_value in wecom_vars.items():
        if var_value:
            print(f"✅ {var_name}: {var_value[:10]}...")
        else:
            print(f"❌ {var_name}: 未设置或为空")

    return all(wecom_vars.values())

if __name__ == "__main__":
    test_environment_variables()