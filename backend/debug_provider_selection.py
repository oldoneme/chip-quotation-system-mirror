#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import get_db
from app.services.unified_approval_service import UnifiedApprovalService

def debug_provider_selection():
    """调试审批提供者选择逻辑"""
    print("🔧 调试审批提供者选择逻辑")
    print("=" * 60)

    db = next(get_db())

    try:
        # 创建统一审批服务
        service = UnifiedApprovalService(db)

        # 检查企业微信提供者可用性
        print("📊 检查企业微信提供者...")
        wecom_provider = service.wecom_provider
        is_wecom_available = wecom_provider.is_available()
        print(f"   企业微信提供者可用: {is_wecom_available}")

        if hasattr(wecom_provider, 'wecom_service'):
            wecom_service = wecom_provider.wecom_service
            print(f"   模板ID: {wecom_service.quote_template_id}")
            print(f"   企业ID: {wecom_service.wecom.corp_id}")
            print(f"   应用ID: {wecom_service.wecom.agent_id}")

        # 检查内部提供者可用性
        print("\n📊 检查内部提供者...")
        internal_provider = service.internal_provider
        is_internal_available = internal_provider.is_available()
        print(f"   内部提供者可用: {is_internal_available}")

        # 测试提供者选择
        print("\n🎯 提供者选择结果...")
        selected_provider = service.select_provider(15)  # 使用测试报价单ID
        provider_type = "企业微信" if hasattr(selected_provider, 'wecom_service') else "内部审批"
        print(f"   选择的提供者: {provider_type}")

        return is_wecom_available and provider_type == "企业微信"

    except Exception as e:
        print(f"❌ 调试异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 开始调试审批提供者选择")

    success = debug_provider_selection()

    print(f"\n🎯 调试结果: {'企业微信提供者正常' if success else '企业微信提供者异常'}")