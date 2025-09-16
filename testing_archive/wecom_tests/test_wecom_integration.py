#!/usr/bin/env python3
"""
企业微信端集成测试
测试企业微信审批系统与统一审批系统的集成情况
"""

import sys
import json
sys.path.append('/home/qixin/projects/chip-quotation-system/backend')

def test_wecom_integration():
    """企业微信集成测试"""
    print("🔍 企业微信端集成测试开始...")

    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "tests": []
    }

    # 1. 检查企业微信配置状态
    print("\n1️⃣ 检查企业微信配置状态")
    try:
        import os
        wecom_configs = {
            'WECOM_CORP_ID': os.getenv('WECOM_CORP_ID'),
            'WECOM_AGENT_ID': os.getenv('WECOM_AGENT_ID'),
            'WECOM_CORP_SECRET': os.getenv('WECOM_CORP_SECRET'),
            'WECOM_QUOTE_TEMPLATE_ID': os.getenv('WECOM_QUOTE_TEMPLATE_ID'),
        }

        configured_count = sum(1 for v in wecom_configs.values() if v)

        results["total_tests"] += 1
        if configured_count > 0:
            print(f"   ✅ 发现 {configured_count}/4 个企业微信配置")
            results["passed"] += 1
            results["tests"].append({"name": "企业微信配置检查", "status": "通过", "detail": f"{configured_count}/4 配置存在"})
        else:
            print("   ⚠️ 未发现企业微信配置（开发环境正常）")
            results["warnings"] += 1
            results["tests"].append({"name": "企业微信配置检查", "status": "警告", "detail": "无配置，将使用内部审批"})

    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "企业微信配置检查", "status": "失败", "detail": str(e)})
        print(f"   ❌ 配置检查失败: {e}")

    # 2. 测试企业微信审批提供者的智能回退
    print("\n2️⃣ 测试企业微信审批提供者智能回退机制")
    try:
        from app.services.wecom_approval_provider import WeComApprovalProvider

        class MockSession:
            def query(self, *args): return self
            def filter(self, *args): return self
            def first(self): return None

        mock_db = MockSession()
        wecom_provider = WeComApprovalProvider(mock_db)

        results["total_tests"] += 1
        # 在没有配置的情况下，应该返回不可用
        is_available = wecom_provider.is_available()
        if is_available is False:
            print("   ✅ 企业微信提供者正确识别为不可用")
            results["passed"] += 1
            results["tests"].append({"name": "企业微信可用性检查", "status": "通过", "detail": "正确返回不可用状态"})
        else:
            print("   ❌ 企业微信提供者可用性检查错误")
            results["failed"] += 1
            results["tests"].append({"name": "企业微信可用性检查", "status": "失败", "detail": "应返回不可用"})

    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "企业微信提供者测试", "status": "失败", "detail": str(e)})
        print(f"   ❌ 企业微信提供者测试失败: {e}")

    # 3. 测试统一审批系统的智能路由（应该选择内部审批）
    print("\n3️⃣ 测试统一审批系统智能路由")
    try:
        from app.services.unified_approval_service import UnifiedApprovalService

        unified_service = UnifiedApprovalService(mock_db)

        results["total_tests"] += 1
        selected_provider = unified_service.select_provider(1)
        provider_name = selected_provider.__class__.__name__

        if provider_name == "InternalApprovalProvider":
            print("   ✅ 统一审批系统正确选择内部审批（企业微信不可用时回退）")
            results["passed"] += 1
            results["tests"].append({"name": "智能路由选择", "status": "通过", "detail": "正确回退到内部审批"})
        else:
            print(f"   ❌ 统一审批系统选择了错误的提供者: {provider_name}")
            results["failed"] += 1
            results["tests"].append({"name": "智能路由选择", "status": "失败", "detail": f"选择了{provider_name}"})

    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "统一审批路由测试", "status": "失败", "detail": str(e)})
        print(f"   ❌ 统一审批路由测试失败: {e}")

    # 4. 测试企业微信API端点（模拟调用）
    print("\n4️⃣ 测试企业微信API端点定义")
    try:
        from app.api.v1.endpoints import wecom_approval

        # 检查关键API端点是否存在
        api_endpoints = [
            'get_approval_status',
            'get_approval_history',
            'approve_quote',
            'reject_quote',
            'create_wecom_approval'
        ]

        results["total_tests"] += 1
        missing_endpoints = []
        for endpoint in api_endpoints:
            if not hasattr(wecom_approval, endpoint):
                missing_endpoints.append(endpoint)

        if not missing_endpoints:
            print("   ✅ 所有企业微信API端点定义完整")
            results["passed"] += 1
            results["tests"].append({"name": "API端点检查", "status": "通过", "detail": f"{len(api_endpoints)}个端点完整"})
        else:
            print(f"   ❌ 缺失API端点: {missing_endpoints}")
            results["failed"] += 1
            results["tests"].append({"name": "API端点检查", "status": "失败", "detail": f"缺失{len(missing_endpoints)}个端点"})

    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "API端点检查", "status": "失败", "detail": str(e)})
        print(f"   ❌ API端点检查失败: {e}")

    # 5. 测试企业微信审批服务存在性
    print("\n5️⃣ 测试企业微信审批服务模块")
    try:
        from app.services.wecom_approval_service import WeComApprovalService

        # 检查关键方法存在性
        service_methods = [
            'submit_quote_approval',
            'approve_quote',
            'reject_quote',
            'check_approval_status'
        ]

        results["total_tests"] += 1
        service = WeComApprovalService(mock_db)
        missing_methods = []
        for method in service_methods:
            if not hasattr(service, method):
                missing_methods.append(method)

        if not missing_methods:
            print("   ✅ 企业微信审批服务方法完整")
            results["passed"] += 1
            results["tests"].append({"name": "审批服务检查", "status": "通过", "detail": f"{len(service_methods)}个方法完整"})
        else:
            print(f"   ❌ 缺失服务方法: {missing_methods}")
            results["failed"] += 1
            results["tests"].append({"name": "审批服务检查", "status": "失败", "detail": f"缺失{len(missing_methods)}个方法"})

    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "审批服务检查", "status": "失败", "detail": str(e)})
        print(f"   ❌ 审批服务检查失败: {e}")

    # 输出测试结果
    print(f"\n📊 企业微信端集成测试结果:")
    print(f"   总计测试: {results['total_tests']}")
    print(f"   通过测试: {results['passed']}")
    print(f"   失败测试: {results['failed']}")
    print(f"   警告提示: {results['warnings']}")
    print(f"   成功率: {(results['passed']/results['total_tests']*100):.1f}%")

    # 详细测试报告
    print(f"\n📋 详细测试报告:")
    for test in results["tests"]:
        status_emoji = {"通过": "✅", "失败": "❌", "警告": "⚠️"}
        emoji = status_emoji.get(test["status"], "❓")
        print(f"   {emoji} {test['name']}: {test['status']} - {test['detail']}")

    print(f"\n💡 企业微信端测试建议:")
    if results["warnings"] > 0:
        print("   📝 当前为开发环境，企业微信未配置属正常情况")
        print("   📝 系统正确回退到内部审批，保证功能可用性")
        print("   📝 如需测试完整企业微信功能，需要配置以下环境变量：")
        print("      - WECOM_CORP_ID: 企业微信企业ID")
        print("      - WECOM_AGENT_ID: 应用Agent ID")
        print("      - WECOM_CORP_SECRET: 应用Secret")
        print("      - WECOM_QUOTE_TEMPLATE_ID: 审批模板ID")

    if results["failed"] == 0:
        print(f"\n🎉 企业微信端集成测试通过！系统在无企业微信配置时正确回退到内部审批")
        return True
    else:
        print(f"\n⚠️ 企业微信端存在{results['failed']}个问题需要修复")
        return False

if __name__ == "__main__":
    test_wecom_integration()