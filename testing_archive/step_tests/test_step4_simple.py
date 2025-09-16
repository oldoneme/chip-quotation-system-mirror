#!/usr/bin/env python3
"""
Step 4 简化集成测试：验证统一审批系统功能
使用requests库避免httpx的代理问题
"""

import requests
import time
import json
import os

# 临时禁用代理
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# 测试配置
BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_QUOTE_ID = "2a72d639-1486-442d-bce3-02a20672de28"

def test_step4_integration():
    """Step 4 统一审批系统集成测试"""
    print("🧪 Step 4 统一审批系统集成测试")
    print("=" * 60)

    test_results = []

    # 测试1: 后端统一审批API
    print("\n🔧 测试1: 后端统一审批API")
    try:
        # 测试状态查询
        response = requests.get(f"{BASE_URL}/api/v1/approval/status/{TEST_QUOTE_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 状态查询成功: {data['quote_number']} -> {data['approval_status']}")
            print(f"   📊 审批方式: {'企业微信' if data['has_wecom_approval'] else '内部审批'}")
            test_results.append(("后端状态查询API", "PASS"))
        else:
            raise Exception(f"状态查询失败: {response.status_code}")

        # 测试历史查询
        response = requests.get(f"{BASE_URL}/api/v1/approval/history/{TEST_QUOTE_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 历史查询成功: {data['total']} 条记录")
            test_results.append(("后端历史查询API", "PASS"))
        else:
            raise Exception(f"历史查询失败: {response.status_code}")

    except Exception as e:
        print(f"   ❌ 后端API测试失败: {e}")
        test_results.append(("后端API测试", "FAIL"))

    # 测试2: 前端可访问性
    print("\n🌐 测试2: 前端应用可访问性")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"   ✅ 前端应用正常运行 (状态码: {response.status_code})")
            test_results.append(("前端可访问性", "PASS"))
        else:
            raise Exception(f"前端访问失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 前端可访问性测试失败: {e}")
        test_results.append(("前端可访问性", "FAIL"))

    # 测试3: API性能测试
    print("\n⚡ 测试3: API性能测试")
    try:
        # 测试API响应时间
        start_time = time.time()
        for _ in range(3):
            requests.get(f"{BASE_URL}/api/v1/approval/status/{TEST_QUOTE_ID}")
        avg_time = (time.time() - start_time) / 3

        if avg_time < 1.0:
            print(f"   ✅ API响应时间正常: {avg_time:.3f}s")
            test_results.append(("API性能", "PASS"))
        else:
            print(f"   ⚠️ API响应时间较慢: {avg_time:.3f}s")
            test_results.append(("API性能", "WARN"))

    except Exception as e:
        print(f"   ❌ API性能测试失败: {e}")
        test_results.append(("API性能", "FAIL"))

    # 测试4: 数据格式验证
    print("\n📊 测试4: API数据格式验证")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/approval/status/{TEST_QUOTE_ID}")
        if response.status_code == 200:
            data = response.json()

            # 验证必要字段
            required_fields = [
                'quote_id', 'quote_number', 'status', 'approval_status',
                'has_wecom_approval'
            ]

            missing_fields = [field for field in required_fields if field not in data]

            if not missing_fields:
                print(f"   ✅ 数据格式验证通过")
                print(f"      包含字段: {', '.join(required_fields)}")

                # 验证数据类型
                if (isinstance(data['quote_id'], str) and
                    isinstance(data['quote_number'], str) and
                    isinstance(data['has_wecom_approval'], bool)):
                    print(f"   ✅ 数据类型验证通过")
                    test_results.append(("数据格式验证", "PASS"))
                else:
                    raise Exception("数据类型不符合预期")
            else:
                raise Exception(f"缺少必要字段: {', '.join(missing_fields)}")
        else:
            raise Exception(f"获取数据失败: {response.status_code}")

    except Exception as e:
        print(f"   ❌ 数据格式验证失败: {e}")
        test_results.append(("数据格式验证", "FAIL"))

    # 测试5: OpenAPI文档验证
    print("\n📚 测试5: OpenAPI文档验证")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()

            # 检查统一审批端点是否在文档中
            paths = openapi_spec.get('paths', {})
            approval_endpoints = [path for path in paths.keys() if '/approval/' in path]

            if len(approval_endpoints) >= 5:  # 应该有5个端点
                print(f"   ✅ OpenAPI文档包含统一审批端点: {len(approval_endpoints)} 个")
                print(f"      端点: {', '.join(approval_endpoints[:3])}...")
                test_results.append(("OpenAPI文档", "PASS"))
            else:
                raise Exception(f"统一审批端点数量不足: {len(approval_endpoints)}")
        else:
            raise Exception(f"获取OpenAPI文档失败: {response.status_code}")

    except Exception as e:
        print(f"   ❌ OpenAPI文档验证失败: {e}")
        test_results.append(("OpenAPI文档", "FAIL"))

    # 打印测试总结
    print("\n" + "=" * 60)
    print("📊 Step 4 集成测试结果总结:")

    pass_count = 0
    warn_count = 0
    fail_count = 0

    for i, (test_name, result) in enumerate(test_results, 1):
        if result == "PASS":
            status = "✅ 通过"
            pass_count += 1
        elif result == "WARN":
            status = "⚠️ 警告"
            warn_count += 1
        else:
            status = "❌ 失败"
            fail_count += 1

        print(f"   测试{i} ({test_name}): {status}")

    print(f"\n总体结果: {pass_count}通过, {warn_count}警告, {fail_count}失败")

    if fail_count == 0:
        print("\n🎉 Step 4 统一审批系统集成测试成功！")
        print("✅ 主要成果:")
        print("   - 后端统一审批API正常工作")
        print("   - 前端应用可正常访问")
        print("   - API性能满足要求")
        print("   - 数据格式符合规范")
        print("   - OpenAPI文档完整")

        print("\n🚀 系统已就绪，可开始使用:")
        print("   - 前端地址: http://localhost:3000")
        print("   - 后端API: http://127.0.0.1:8000/api/v1/approval/")
        print("   - API文档: http://127.0.0.1:8000/docs")

        return True
    else:
        print(f"\n⚠️ {fail_count} 个测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = test_step4_integration()
    exit(0 if success else 1)