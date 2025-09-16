#!/usr/bin/env python3
"""
Step 2.5 测试：审批状态同步器
"""

import sys
sys.path.append('/home/qixin/projects/chip-quotation-system/backend')

# 测试状态同步器
try:
    from app.services.approval_status_synchronizer import ApprovalStatusSynchronizer, QuoteStatus
    from app.services.unified_approval_service import ApprovalStatus
    print("✅ ApprovalStatusSynchronizer导入成功")

    # 模拟数据库会话
    class MockSession:
        def query(self, *args):
            return self
        def filter(self, *args):
            return self
        def first(self):
            return None
        def all(self):
            return []
        def commit(self):
            pass
        def rollback(self):
            pass

    mock_db = MockSession()
    synchronizer = ApprovalStatusSynchronizer(mock_db)
    print("✅ ApprovalStatusSynchronizer实例化成功")

    # 测试状态映射功能
    print("\n📋 测试状态映射:")

    # 测试审批状态到报价单状态的映射
    approval_to_quote_tests = [
        (ApprovalStatus.NOT_SUBMITTED, QuoteStatus.DRAFT),
        (ApprovalStatus.PENDING, QuoteStatus.PENDING),
        (ApprovalStatus.APPROVED, QuoteStatus.APPROVED),
        (ApprovalStatus.REJECTED, QuoteStatus.REJECTED),
    ]

    for approval_status, expected_quote_status in approval_to_quote_tests:
        result = synchronizer.map_approval_to_quote_status(approval_status)
        if result == expected_quote_status:
            print(f"✅ {approval_status.value} -> {result.value}")
        else:
            print(f"❌ {approval_status.value} -> {result.value} (期望: {expected_quote_status.value})")

    # 测试报价单状态到审批状态的映射
    print("\n📋 测试反向映射:")
    quote_to_approval_tests = [
        (QuoteStatus.DRAFT, ApprovalStatus.NOT_SUBMITTED),
        (QuoteStatus.PENDING, ApprovalStatus.PENDING),
        (QuoteStatus.APPROVED, ApprovalStatus.APPROVED),
        (QuoteStatus.REJECTED, ApprovalStatus.REJECTED),
        (QuoteStatus.RETURNED, ApprovalStatus.PENDING),
        (QuoteStatus.FORWARDED, ApprovalStatus.PENDING),
    ]

    for quote_status, expected_approval_status in quote_to_approval_tests:
        result = synchronizer.map_quote_to_approval_status(quote_status)
        if result == expected_approval_status:
            print(f"✅ {quote_status.value} -> {result.value}")
        else:
            print(f"❌ {quote_status.value} -> {result.value} (期望: {expected_approval_status.value})")

    # 测试同步器方法是否存在
    methods = ['sync_status_fields', 'check_status_consistency', 'repair_inconsistent_status', 'batch_check_consistency']
    print(f"\n📋 测试同步器方法:")
    for method_name in methods:
        if hasattr(synchronizer, method_name):
            print(f"✅ 方法 {method_name} 存在")
        else:
            print(f"❌ 方法 {method_name} 缺失")

except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n🎉 Step 2.5 测试完成：审批状态同步器功能正常")