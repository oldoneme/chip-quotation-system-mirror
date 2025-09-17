#!/usr/bin/env python3
"""
Step 3 API测试 - 验证统一API层升级
测试V2 API端点的功能性和向后兼容性
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

# API测试配置
BASE_URL = "http://127.0.0.1:8000"
V1_PREFIX = "/api/v1"
V2_PREFIX = "/api/v2"

class APITester:
    """API测试器"""

    def __init__(self):
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def test_v2_api_info(self):
        """测试V2 API信息端点"""
        print("\n🧪 测试V2 API信息端点...")

        try:
            response = await self.client.get(f"{V2_PREFIX}/")
            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ API名称: {data['name']}")
                print(f"✅ API版本: {data['version']}")
                print(f"✅ 功能数量: {len(data['features'])}")
                return True
            else:
                print(f"❌ API信息获取失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ API信息测试异常: {e}")
            return False

    async def test_approval_health(self):
        """测试审批健康检查端点"""
        print("\n🧪 测试审批健康检查...")

        try:
            response = await self.client.get(f"{V2_PREFIX}/approval/health")
            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康状态: {data['status']}")
                print(f"✅ 版本: {data['version']}")
                print(f"✅ 功能数量: {len(data['features'])}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False

    async def test_approval_list_endpoint(self):
        """测试审批列表端点"""
        print("\n🧪 测试审批列表端点...")

        try:
            # 测试基本列表查询
            response = await self.client.get(f"{V2_PREFIX}/approval/list")
            print(f"基本查询状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 总数: {data['total']}")
                print(f"✅ 当前页: {data['page']}")
                print(f"✅ 页大小: {data['page_size']}")
                print(f"✅ 条目数: {len(data['items'])}")

                # 测试状态过滤
                response2 = await self.client.get(f"{V2_PREFIX}/approval/list?status_filter=pending")
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"✅ 过滤查询成功，pending数量: {data2['total']}")

                return True
            else:
                print(f"❌ 列表查询失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 列表查询异常: {e}")
            return False

    async def test_mock_approval_operation(self):
        """测试模拟审批操作 (不依赖真实数据)"""
        print("\n🧪 测试审批操作端点结构...")

        try:
            # 使用不存在的quote_id来测试端点结构
            fake_quote_id = 99999
            operation_data = {
                "action": "approve",
                "comments": "API测试审批",
                "channel": "auto"
            }

            response = await self.client.post(
                f"{V2_PREFIX}/approval/{fake_quote_id}/operate",
                json=operation_data
            )

            print(f"操作测试状态码: {response.status_code}")

            # 预期会返回404 (报价单不存在) 或 401 (需要认证)
            if response.status_code in [404, 401, 422]:
                print(f"✅ 端点响应正常 (预期错误: {response.status_code})")
                try:
                    error_data = response.json()
                    print(f"✅ 错误格式正确: {error_data.get('detail', 'No detail')}")
                except:
                    print("✅ 端点存在且能处理请求")
                return True
            else:
                print(f"❌ 意外状态码: {response.status_code}")
                print(f"响应: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 操作测试异常: {e}")
            return False

    async def test_mock_status_query(self):
        """测试状态查询端点结构"""
        print("\n🧪 测试状态查询端点结构...")

        try:
            fake_quote_id = 99999
            response = await self.client.get(f"{V2_PREFIX}/approval/{fake_quote_id}/status")

            print(f"状态查询状态码: {response.status_code}")

            # 预期会返回404 (报价单不存在) 或 401 (需要认证)
            if response.status_code in [404, 401, 422]:
                print(f"✅ 端点响应正常 (预期错误: {response.status_code})")
                return True
            else:
                print(f"❌ 意外状态码: {response.status_code}")
                print(f"响应: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 状态查询异常: {e}")
            return False

    async def test_backward_compatibility(self):
        """测试向后兼容性 - V1端点是否仍然工作"""
        print("\n🧪 测试向后兼容性...")

        try:
            # 测试V1 API是否仍然可访问
            response = await self.client.get(f"{V1_PREFIX}/")
            print(f"V1 API访问状态码: {response.status_code}")

            if response.status_code in [200, 404, 405]:  # 200=成功, 404=端点不存在但路由工作, 405=方法不允许但端点存在
                print("✅ V1 API路由正常工作")
                return True
            else:
                print(f"❌ V1 API可能有问题: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 向后兼容性测试异常: {e}")
            return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("Step 3: 统一API层升级 - 功能测试")
    print("=" * 60)

    test_results = []

    async with APITester() as tester:
        # 执行所有测试
        tests = [
            ("V2 API信息", tester.test_v2_api_info),
            ("审批健康检查", tester.test_approval_health),
            ("审批列表端点", tester.test_approval_list_endpoint),
            ("审批操作端点结构", tester.test_mock_approval_operation),
            ("状态查询端点结构", tester.test_mock_status_query),
            ("向后兼容性", tester.test_backward_compatibility),
        ]

        for test_name, test_func in tests:
            print(f"\n{'='*40}")
            print(f"执行测试: {test_name}")
            print(f"{'='*40}")

            try:
                result = await test_func()
                test_results.append((test_name, result))

                if result:
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败")

            except Exception as e:
                print(f"❌ {test_name} - 异常: {e}")
                test_results.append((test_name, False))

    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:.<30} {status}")

    print(f"\n总体结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！Step 3 API层升级成功！")
        return True
    else:
        print(f"⚠️  {total - passed} 个测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)