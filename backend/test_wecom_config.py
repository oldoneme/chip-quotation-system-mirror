#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import get_db
from app.services.wecom_approval_provider import WeComApprovalProvider

def test_wecom_configuration():
    """测试企业微信配置是否正确"""
    print("🔧 测试企业微信审批配置")
    print("=" * 50)

    # 获取数据库连接
    db = next(get_db())

    try:
        # 创建企业微信审批提供者
        provider = WeComApprovalProvider(db)

        # 检查服务可用性
        is_available = provider.is_available()
        print(f"📊 企业微信审批服务可用性: {is_available}")

        # 获取详细信息
        wecom_service = provider.wecom_service
        print(f"📝 模板ID: {wecom_service.quote_template_id}")
        print(f"🏢 企业ID: {wecom_service.wecom.corp_id}")
        print(f"🎯 应用ID: {wecom_service.wecom.agent_id}")

        if is_available:
            print("✅ 企业微信审批配置正确，可以发送通知")
        else:
            print("❌ 企业微信审批配置不完整，无法发送通知")

        return is_available

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_wecom_configuration()