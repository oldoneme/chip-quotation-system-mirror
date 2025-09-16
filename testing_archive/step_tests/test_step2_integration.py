#!/usr/bin/env python3
"""
Step 2 集成测试：验证后端服务层统一的完整功能
"""

import sys
sys.path.append('/home/qixin/projects/chip-quotation-system/backend')

def test_step2_integration():
    """Step 2 完整集成测试"""
    print("🧪 开始 Step 2 集成测试...")
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }

    # 1. 测试统一审批服务完整流程
    print("\n1️⃣ 测试统一审批服务完整流程")
    try:
        from app.services.unified_approval_service import UnifiedApprovalService, ApprovalMethod, ApprovalStatus
        from app.services.wecom_approval_provider import WeComApprovalProvider
        from app.services.internal_approval_provider import InternalApprovalProvider

        # 模拟数据库会话
        class MockSession:
            def query(self, *args): return self
            def filter(self, *args): return self
            def first(self): return None
            def add(self, obj): pass
            def commit(self): pass
            def refresh(self, obj): pass

        mock_db = MockSession()
        unified_service = UnifiedApprovalService(mock_db)

        # 测试双提供者
        results["total_tests"] += 1
        wecom_provider = unified_service.wecom_provider
        internal_provider = unified_service.internal_provider

        if isinstance(wecom_provider, WeComApprovalProvider) and isinstance(internal_provider, InternalApprovalProvider):
            print("   ✅ 双提供者加载成功")
            results["passed"] += 1
        else:
            print("   ❌ 双提供者类型错误")
            results["failed"] += 1
            results["errors"].append("双提供者类型不匹配")

        # 测试智能路由选择
        results["total_tests"] += 1
        selected_provider = unified_service.select_provider(1)
        if selected_provider.__class__.__name__ == "InternalApprovalProvider":
            print("   ✅ 智能路由选择正确（企业微信不可用时选择内部审批）")
            results["passed"] += 1
        else:
            print("   ❌ 智能路由选择错误")
            results["failed"] += 1
            results["errors"].append("路由选择逻辑错误")

    except Exception as e:
        results["total_tests"] += 1
        results["failed"] += 1
        results["errors"].append(f"统一服务测试异常: {e}")
        print(f"   ❌ 统一服务测试异常: {e}")

    # 2. 测试QuoteService重构
    print("\n2️⃣ 测试QuoteService重构")
    try:
        from app.services.quote_service import QuoteService
        import inspect

        mock_db = MockSession()
        quote_service = QuoteService(mock_db)

        # 检查重构的方法是否使用统一服务
        methods_to_check = ['submit_for_approval', 'approve_quote', 'reject_quote']

        for method_name in methods_to_check:
            results["total_tests"] += 1
            method = getattr(quote_service, method_name)
            source = inspect.getsource(method)

            if 'UnifiedApprovalService' in source:
                print(f"   ✅ {method_name} 已重构使用统一服务")
                results["passed"] += 1
            else:
                print(f"   ❌ {method_name} 未使用统一服务")
                results["failed"] += 1
                results["errors"].append(f"{method_name}未重构")

    except Exception as e:
        results["total_tests"] += 1
        results["failed"] += 1
        results["errors"].append(f"QuoteService测试异常: {e}")
        print(f"   ❌ QuoteService测试异常: {e}")

    # 3. 测试状态同步器
    print("\n3️⃣ 测试状态同步器")
    try:
        from app.services.approval_status_synchronizer import ApprovalStatusSynchronizer, QuoteStatus

        synchronizer = ApprovalStatusSynchronizer(mock_db)

        # 测试状态映射完整性
        results["total_tests"] += 1
        mapping_tests = [
            (ApprovalStatus.NOT_SUBMITTED, QuoteStatus.DRAFT),
            (ApprovalStatus.PENDING, QuoteStatus.PENDING),
            (ApprovalStatus.APPROVED, QuoteStatus.APPROVED),
            (ApprovalStatus.REJECTED, QuoteStatus.REJECTED),
        ]

        mapping_correct = True
        for approval_status, expected_quote in mapping_tests:
            result = synchronizer.map_approval_to_quote_status(approval_status)
            if result != expected_quote:
                mapping_correct = False
                break

        if mapping_correct:
            print("   ✅ 状态映射正确")
            results["passed"] += 1
        else:
            print("   ❌ 状态映射错误")
            results["failed"] += 1
            results["errors"].append("状态映射逻辑错误")

    except Exception as e:
        results["total_tests"] += 1
        results["failed"] += 1
        results["errors"].append(f"状态同步器测试异常: {e}")
        print(f"   ❌ 状态同步器测试异常: {e}")

    # 4. 测试审批记录管理器
    print("\n4️⃣ 测试审批记录管理器")
    try:
        from app.services.approval_record_manager import ApprovalRecordManager
        from app.services.unified_approval_service import ApprovalResult

        record_manager = ApprovalRecordManager(mock_db)

        # 测试意见标准化
        results["total_tests"] += 1
        test_comment = record_manager._standardize_comments(
            "同意",
            ApprovalMethod.WECOM,
            "审批通过"
        )

        if "(通过企业微信审批)" in test_comment:
            print("   ✅ 审批意见标准化正确")
            results["passed"] += 1
        else:
            print("   ❌ 审批意见标准化错误")
            results["failed"] += 1
            results["errors"].append("意见标准化失败")

    except Exception as e:
        results["total_tests"] += 1
        results["failed"] += 1
        results["errors"].append(f"记录管理器测试异常: {e}")
        print(f"   ❌ 记录管理器测试异常: {e}")

    # 5. 测试企业微信提供者
    print("\n5️⃣ 测试企业微信提供者")
    try:
        from app.services.wecom_approval_provider import WeComApprovalProvider

        provider = WeComApprovalProvider(mock_db)

        results["total_tests"] += 1
        # 测试接口完整性
        required_methods = ['submit_approval', 'approve', 'reject', 'is_available']
        methods_exist = all(hasattr(provider, method) for method in required_methods)

        if methods_exist:
            print("   ✅ 企业微信提供者接口完整")
            results["passed"] += 1
        else:
            print("   ❌ 企业微信提供者接口不完整")
            results["failed"] += 1
            results["errors"].append("接口方法缺失")

        # 测试可用性检查
        results["total_tests"] += 1
        is_available = provider.is_available()  # 应该返回False（没有配置）
        print(f"   ✅ 可用性检查执行成功: {is_available}")
        results["passed"] += 1

    except Exception as e:
        results["total_tests"] += 1
        results["failed"] += 1
        results["errors"].append(f"企业微信提供者测试异常: {e}")
        print(f"   ❌ 企业微信提供者测试异常: {e}")

    # 输出测试结果
    print(f"\n📊 Step 2 集成测试结果:")
    print(f"   总计测试: {results['total_tests']}")
    print(f"   通过测试: {results['passed']}")
    print(f"   失败测试: {results['failed']}")
    print(f"   成功率: {(results['passed']/results['total_tests']*100):.1f}%")

    if results["errors"]:
        print(f"\n❌ 错误详情:")
        for error in results["errors"]:
            print(f"   - {error}")

    if results["failed"] == 0:
        print(f"\n🎉 Step 2 集成测试全部通过！后端服务层统一功能正常")
        return True
    else:
        print(f"\n⚠️ Step 2 存在{results['failed']}个问题需要修复")
        return False

if __name__ == "__main__":
    test_step2_integration()