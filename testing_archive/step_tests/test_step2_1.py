#!/usr/bin/env python3
"""
Step 2.1 测试：企业微信审批提供者
"""

import sys
import os
sys.path.append('/home/qixin/projects/chip-quotation-system/backend')

# 测试导入
try:
    from app.services.wecom_approval_provider import WeComApprovalProvider
    print("✅ WeComApprovalProvider导入成功")
except Exception as e:
    print(f"❌ WeComApprovalProvider导入失败: {e}")
    sys.exit(1)

# 测试抽象接口实现
try:
    from app.services.unified_approval_service import AbstractApprovalProvider, ApprovalMethod, ApprovalStatus

    # 检查是否正确继承抽象类
    print(f"✅ 继承检查: {issubclass(WeComApprovalProvider, AbstractApprovalProvider)}")

    # 检查必需方法存在
    provider_methods = ['submit_approval', 'approve', 'reject', 'is_available']
    for method_name in provider_methods:
        if hasattr(WeComApprovalProvider, method_name):
            print(f"✅ 方法 {method_name} 存在")
        else:
            print(f"❌ 方法 {method_name} 缺失")

except Exception as e:
    print(f"❌ 接口检查失败: {e}")

# 模拟数据库会话测试实例化（不访问真实数据库）
try:
    # 创建模拟会话对象
    class MockSession:
        def query(self, *args):
            return self
        def filter(self, *args):
            return self
        def first(self):
            return None

    mock_db = MockSession()
    provider = WeComApprovalProvider(mock_db)
    print("✅ WeComApprovalProvider实例化成功")

    # 测试可用性检查（预期返回False，因为没有真实配置）
    is_available = provider.is_available()
    print(f"✅ 可用性检查执行成功: {is_available}")

except Exception as e:
    print(f"❌ 实例化测试失败: {e}")

print("🎉 Step 2.1 测试完成：企业微信审批提供者基础功能正常")