#!/usr/bin/env python3
"""
Step 4 集成测试：验证前后端统一审批系统的完整集成
测试从后端API到前端组件的完整数据流
"""

import asyncio
import json
from typing import Dict, Any, List

import httpx

# 测试配置
BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"

# 测试用的报价单ID（从现有数据中选择）
TEST_QUOTE_ID = "2a72d639-1486-442d-bce3-02a20672de28"  # 已知存在的报价单

class Step4IntegrationTest:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.test_results = []

    async def run_all_tests(self):
        """运行所有集成测试"""
        print("🧪 Step 4 统一审批系统集成测试")
        print("=" * 60)

        try:
            # 1. 后端API测试
            await self.test_backend_apis()

            # 2. 前端可访问性测试
            await self.test_frontend_accessibility()

            # 3. API数据格式测试
            await self.test_api_data_formats()

            # 4. 完整工作流测试
            await self.test_complete_workflow()

            self.print_summary()

        except Exception as e:
            print(f"💥 集成测试执行异常: {e}")
        finally:
            await self.client.aclose()

    async def test_backend_apis(self):
        """测试后端统一审批API"""
        print("\n🔧 测试1: 后端统一审批API")

        try:
            # 测试状态查询API
            response = await self.client.get(f"{BASE_URL}/api/v1/approval/status/{TEST_QUOTE_ID}")

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 状态查询成功: {data['quote_number']} -> {data['approval_status']}")
                self.test_results.append({
                    "test": "后端状态查询API",
                    "result": "PASS",
                    "data": data
                })
            else:
                raise Exception(f"状态查询失败: {response.status_code}")

            # 测试历史查询API
            response = await self.client.get(f"{BASE_URL}/api/v1/approval/history/{TEST_QUOTE_ID}")

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 历史查询成功: {data['total']} 条记录")
                self.test_results.append({
                    "test": "后端历史查询API",
                    "result": "PASS",
                    "data": data
                })
            else:
                raise Exception(f"历史查询失败: {response.status_code}")

        except Exception as e:
            print(f"   ❌ 后端API测试失败: {e}")
            self.test_results.append({
                "test": "后端API测试",
                "result": "FAIL",
                "error": str(e)
            })

    async def test_frontend_accessibility(self):
        """测试前端可访问性"""
        print("\n🌐 测试2: 前端应用可访问性")

        try:
            # 测试前端主页
            response = await self.client.get(FRONTEND_URL)

            if response.status_code == 200:
                content = response.text
                if "React" in content or "chip-quotation" in content:
                    print(f"   ✅ 前端应用正常运行")
                    self.test_results.append({
                        "test": "前端可访问性",
                        "result": "PASS"
                    })
                else:
                    raise Exception("前端内容不符合预期")
            else:
                raise Exception(f"前端访问失败: {response.status_code}")

        except Exception as e:
            print(f"   ❌ 前端可访问性测试失败: {e}")
            self.test_results.append({
                "test": "前端可访问性",
                "result": "FAIL",
                "error": str(e)
            })

    async def test_api_data_formats(self):
        """测试API数据格式兼容性"""
        print("\n📊 测试3: API数据格式兼容性")

        try:
            # 获取状态数据并验证格式
            response = await self.client.get(f"{BASE_URL}/api/v1/approval/status/{TEST_QUOTE_ID}")

            if response.status_code == 200:
                data = response.json()

                # 验证必要字段
                required_fields = [
                    'quote_id', 'quote_number', 'status', 'approval_status',
                    'has_wecom_approval'
                ]

                missing_fields = [field for field in required_fields if field not in data]

                if not missing_fields:
                    print(f"   ✅ API数据格式验证通过")
                    print(f"      包含所有必要字段: {', '.join(required_fields)}")

                    # 验证数据类型
                    type_checks = [
                        (data['quote_id'], str, "quote_id should be string"),
                        (data['quote_number'], str, "quote_number should be string"),
                        (data['has_wecom_approval'], bool, "has_wecom_approval should be boolean")
                    ]

                    type_errors = []
                    for value, expected_type, message in type_checks:
                        if not isinstance(value, expected_type):
                            type_errors.append(message)

                    if not type_errors:
                        print(f"   ✅ 数据类型验证通过")
                        self.test_results.append({
                            "test": "API数据格式",
                            "result": "PASS"
                        })
                    else:
                        raise Exception(f"数据类型错误: {', '.join(type_errors)}")
                else:
                    raise Exception(f"缺少必要字段: {', '.join(missing_fields)}")
            else:
                raise Exception(f"获取数据失败: {response.status_code}")

        except Exception as e:
            print(f"   ❌ API数据格式测试失败: {e}")
            self.test_results.append({
                "test": "API数据格式",
                "result": "FAIL",
                "error": str(e)
            })

    async def test_complete_workflow(self):
        """测试完整工作流"""
        print("\n🔄 测试4: 完整审批工作流")

        try:
            # 1. 获取报价单状态
            status_response = await self.client.get(f"{BASE_URL}/api/v1/approval/status/{TEST_QUOTE_ID}")

            if status_response.status_code != 200:
                raise Exception(f"获取状态失败: {status_response.status_code}")

            status_data = status_response.json()
            current_status = status_data['approval_status']

            print(f"   📋 当前状态: {current_status}")

            # 2. 获取审批历史
            history_response = await self.client.get(f"{BASE_URL}/api/v1/approval/history/{TEST_QUOTE_ID}")

            if history_response.status_code != 200:
                raise Exception(f"获取历史失败: {history_response.status_code}")

            history_data = history_response.json()

            print(f"   📚 历史记录: {history_data['total']} 条")

            # 3. 验证状态一致性
            if status_data['quote_id'] == TEST_QUOTE_ID and history_data['quote_id'] == TEST_QUOTE_ID:
                print(f"   ✅ 数据一致性验证通过")

                # 4. 验证API响应时间
                import time
                start_time = time.time()

                for _ in range(3):
                    await self.client.get(f"{BASE_URL}/api/v1/approval/status/{TEST_QUOTE_ID}")

                avg_time = (time.time() - start_time) / 3

                if avg_time < 1.0:  # 响应时间小于1秒
                    print(f"   ✅ API响应时间验证通过: {avg_time:.3f}s")

                    self.test_results.append({
                        "test": "完整工作流",
                        "result": "PASS",
                        "metrics": {
                            "avg_response_time": avg_time,
                            "current_status": current_status,
                            "history_count": history_data['total']
                        }
                    })
                else:
                    raise Exception(f"API响应时间过长: {avg_time:.3f}s")
            else:
                raise Exception("数据一致性验证失败")

        except Exception as e:
            print(f"   ❌ 完整工作流测试失败: {e}")
            self.test_results.append({
                "test": "完整工作流",
                "result": "FAIL",
                "error": str(e)
            })

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 Step 4 集成测试结果总结:")

        pass_count = 0
        fail_count = 0

        for i, result in enumerate(self.test_results, 1):
            status = "✅ 通过" if result["result"] == "PASS" else "❌ 失败"
            print(f"   测试{i} ({result['test']}): {status}")

            if result["result"] == "PASS":
                pass_count += 1
                # 显示额外指标
                if "metrics" in result:
                    metrics = result["metrics"]
                    print(f"      📊 性能指标: 响应时间 {metrics.get('avg_response_time', 0):.3f}s")
            else:
                fail_count += 1
                if "error" in result:
                    print(f"      ❌ 错误: {result['error']}")

        print(f"\n总体结果: {pass_count}/{len(self.test_results)} 测试通过")

        if fail_count == 0:
            print("\n🎉 Step 4 统一审批系统集成测试全部通过！")
            print("✅ 前后端集成成功，统一审批界面已就绪")
            print("\n🚀 可以开始使用统一审批功能:")
            print("   - 前端应用: http://localhost:3000")
            print("   - 统一API: /api/v1/approval/")
            print("   - Swagger文档: http://127.0.0.1:8000/docs")
            return True
        else:
            print(f"\n⚠️ {fail_count} 个测试失败，需要进一步检查")
            return False

async def main():
    """主测试入口"""
    test_runner = Step4IntegrationTest()
    success = await test_runner.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)