#!/usr/bin/env python3
"""
调试状态映射问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.unified_approval_service import ApprovalStatus
from app.services.approval_status_synchronizer import ApprovalStatusSynchronizer, QuoteStatus

def test_mapping():
    """测试状态映射逻辑"""
    print("🧪 测试状态映射逻辑")

    # 测试关键映射
    test_cases = [
        (ApprovalStatus.NOT_SUBMITTED, "not_submitted"),
        (ApprovalStatus.PENDING, "pending"),
        (ApprovalStatus.APPROVED, "approved"),
        (ApprovalStatus.REJECTED, "rejected"),
    ]

    for approval_status, status_str in test_cases:
        result = ApprovalStatusSynchronizer.map_approval_to_quote_status(approval_status)
        print(f"   {approval_status} ({status_str}) -> {result} ({result.value})")

        # 验证特定映射
        if approval_status == ApprovalStatus.PENDING:
            if result == QuoteStatus.PENDING:
                print(f"   ✅ PENDING映射正确")
            else:
                print(f"   ❌ PENDING映射错误: 期望 {QuoteStatus.PENDING}, 实际 {result}")

    print(f"\n🔍 枚举值对比:")
    print(f"   ApprovalStatus.PENDING = {ApprovalStatus.PENDING} (value: {ApprovalStatus.PENDING.value})")
    print(f"   QuoteStatus.PENDING = {QuoteStatus.PENDING} (value: {QuoteStatus.PENDING.value})")

if __name__ == "__main__":
    test_mapping()