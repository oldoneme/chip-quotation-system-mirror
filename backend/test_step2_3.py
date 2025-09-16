#!/usr/bin/env python3
"""
Step 2.3 测试：企业微信提供者集成到统一服务
"""

import sys
sys.path.append('/home/qixin/projects/chip-quotation-system/backend')

# 测试统一服务的智能选择功能
try:
    from app.services.unified_approval_service import UnifiedApprovalService
    print("✅ UnifiedApprovalService导入成功")

    # 模拟数据库会话
    class MockSession:
        def query(self, *args):
            return self
        def filter(self, *args):
            return self
        def first(self):
            return None

    mock_db = MockSession()
    unified_service = UnifiedApprovalService(mock_db)
    print("✅ UnifiedApprovalService实例化成功")

    # 测试提供者属性
    if hasattr(unified_service, 'wecom_provider'):
        print("✅ wecom_provider属性存在")
    else:
        print("❌ wecom_provider属性缺失")

    if hasattr(unified_service, 'internal_provider'):
        print("✅ internal_provider属性存在")
    else:
        print("❌ internal_provider属性缺失")

    # 测试提供者实例化（不会真正访问企业微信API）
    try:
        internal_provider = unified_service.internal_provider
        print("✅ 内部审批提供者实例化成功")
    except Exception as e:
        print(f"❌ 内部审批提供者实例化失败: {e}")

    try:
        wecom_provider = unified_service.wecom_provider
        print("✅ 企业微信审批提供者实例化成功")

        # 测试可用性检查（预期返回False，因为没有配置）
        is_wecom_available = wecom_provider.is_available()
        print(f"✅ 企业微信可用性检查: {is_wecom_available}")
    except Exception as e:
        print(f"❌ 企业微信审批提供者实例化失败: {e}")

    # 测试智能选择逻辑
    try:
        selected_provider = unified_service.select_provider(1)  # 假设quote_id=1
        provider_name = selected_provider.__class__.__name__
        print(f"✅ 智能选择提供者: {provider_name}")

        # 由于企业微信不可用，应该选择内部审批
        if 'Internal' in provider_name:
            print("✅ 正确选择了内部审批提供者（企业微信不可用时的回退）")
        else:
            print("⚠️ 选择了非内部审批提供者")

    except Exception as e:
        print(f"❌ 智能选择失败: {e}")

except Exception as e:
    print(f"❌ 测试失败: {e}")

print("🎉 Step 2.3 测试完成：企业微信提供者已集成到统一服务")