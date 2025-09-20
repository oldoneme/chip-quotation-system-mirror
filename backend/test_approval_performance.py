#!/usr/bin/env python3
"""
统一审批系统性能测试
测试API响应时间和并发性能
"""

import sys
import os
import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
import json

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API配置
BASE_URL = "http://127.0.0.1:8000"
API_V2_BASE = f"{BASE_URL}/api/v2/approval"

class PerformanceTest:
    """性能测试类"""

    def __init__(self):
        self.session = None
        self.results = []

    async def setup_session(self):
        """设置HTTP会话"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        logger.info("HTTP会话已建立")

    async def cleanup_session(self):
        """清理HTTP会话"""
        if self.session:
            await self.session.close()
            logger.info("HTTP会话已关闭")

    async def test_api_response_time(self, endpoint: str, method: str = "GET", data: dict = None, repeat: int = 100):
        """测试API响应时间"""
        test_name = f"{method} {endpoint}"
        logger.info(f"开始性能测试: {test_name} (重复 {repeat} 次)")

        response_times = []
        success_count = 0
        error_count = 0

        for i in range(repeat):
            start_time = time.time()

            try:
                if method.upper() == "GET":
                    async with self.session.get(f"{API_V2_BASE}{endpoint}") as response:
                        await response.read()
                        if response.status == 200:
                            success_count += 1
                        else:
                            error_count += 1
                elif method.upper() == "POST":
                    async with self.session.post(
                        f"{API_V2_BASE}{endpoint}",
                        json=data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        await response.read()
                        if response.status == 200:
                            success_count += 1
                        else:
                            error_count += 1

                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                response_times.append(response_time)

            except Exception as e:
                error_count += 1
                logger.warning(f"请求失败: {e}")

            # 每10次输出进度
            if (i + 1) % 10 == 0:
                logger.info(f"进度: {i + 1}/{repeat}")

        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

            result = {
                'test_name': test_name,
                'total_requests': repeat,
                'success_count': success_count,
                'error_count': error_count,
                'avg_response_time': round(avg_time, 2),
                'min_response_time': round(min_time, 2),
                'max_response_time': round(max_time, 2),
                'p95_response_time': round(p95_time, 2),
                'success_rate': round((success_count / repeat) * 100, 2)
            }

            self.results.append(result)
            logger.info(f"✅ {test_name} 完成:")
            logger.info(f"   成功率: {result['success_rate']}%")
            logger.info(f"   平均响应时间: {result['avg_response_time']}ms")
            logger.info(f"   P95响应时间: {result['p95_response_time']}ms")

        else:
            logger.error(f"❌ {test_name} 所有请求都失败了")

    async def test_concurrent_requests(self, endpoint: str, concurrent_users: int = 10, requests_per_user: int = 5):
        """测试并发请求性能"""
        test_name = f"并发测试 {endpoint} ({concurrent_users}用户 x {requests_per_user}请求)"
        logger.info(f"开始并发测试: {test_name}")

        async def user_requests():
            """单个用户的请求"""
            user_times = []
            for _ in range(requests_per_user):
                start_time = time.time()
                try:
                    async with self.session.get(f"{API_V2_BASE}{endpoint}") as response:
                        await response.read()
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000
                        user_times.append(response_time)
                except Exception as e:
                    logger.warning(f"并发请求失败: {e}")
            return user_times

        # 启动并发任务
        start_time = time.time()
        tasks = [user_requests() for _ in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        end_time = time.time()

        # 收集结果
        all_times = []
        for user_times in all_results:
            all_times.extend(user_times)

        total_requests = concurrent_users * requests_per_user
        total_time = (end_time - start_time) * 1000

        if all_times:
            avg_time = statistics.mean(all_times)
            throughput = len(all_times) / (total_time / 1000)  # 请求/秒

            result = {
                'test_name': test_name,
                'concurrent_users': concurrent_users,
                'requests_per_user': requests_per_user,
                'total_requests': total_requests,
                'successful_requests': len(all_times),
                'total_time': round(total_time, 2),
                'avg_response_time': round(avg_time, 2),
                'throughput': round(throughput, 2),
                'success_rate': round((len(all_times) / total_requests) * 100, 2)
            }

            self.results.append(result)
            logger.info(f"✅ {test_name} 完成:")
            logger.info(f"   成功率: {result['success_rate']}%")
            logger.info(f"   吞吐量: {result['throughput']} 请求/秒")
            logger.info(f"   平均响应时间: {result['avg_response_time']}ms")

    async def run_performance_tests(self):
        """运行完整的性能测试套件"""
        logger.info("🚀 开始性能测试")

        # 1. API健康检查性能
        await self.test_api_response_time("/health", repeat=50)

        # 2. 审批列表查询性能
        await self.test_api_response_time("/list?page=1&page_size=10", repeat=50)

        # 3. 并发测试 - 健康检查
        await self.test_concurrent_requests("/health", concurrent_users=10, requests_per_user=5)

        # 4. 并发测试 - 审批列表
        await self.test_concurrent_requests("/list?page=1&page_size=10", concurrent_users=5, requests_per_user=3)

        logger.info("✅ 性能测试完成")

    def print_performance_report(self):
        """打印性能测试报告"""
        print("\n" + "=" * 80)
        print("📊 统一审批系统性能测试报告")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        for result in self.results:
            print(f"测试项目: {result['test_name']}")

            if 'concurrent_users' in result:
                # 并发测试结果
                print(f"  并发用户数: {result['concurrent_users']}")
                print(f"  每用户请求数: {result['requests_per_user']}")
                print(f"  总请求数: {result['total_requests']}")
                print(f"  成功请求数: {result['successful_requests']}")
                print(f"  成功率: {result['success_rate']}%")
                print(f"  总耗时: {result['total_time']}ms")
                print(f"  平均响应时间: {result['avg_response_time']}ms")
                print(f"  吞吐量: {result['throughput']} 请求/秒")
            else:
                # 响应时间测试结果
                print(f"  总请求数: {result['total_requests']}")
                print(f"  成功数: {result['success_count']}")
                print(f"  失败数: {result['error_count']}")
                print(f"  成功率: {result['success_rate']}%")
                print(f"  平均响应时间: {result['avg_response_time']}ms")
                print(f"  最小响应时间: {result['min_response_time']}ms")
                print(f"  最大响应时间: {result['max_response_time']}ms")
                print(f"  P95响应时间: {result['p95_response_time']}ms")

            print()

        # 性能评估
        print("-" * 80)
        print("🎯 性能评估")
        print("-" * 80)

        avg_response_times = []
        success_rates = []

        for result in self.results:
            if 'avg_response_time' in result:
                avg_response_times.append(result['avg_response_time'])
                success_rates.append(result['success_rate'])

        if avg_response_times:
            overall_avg = statistics.mean(avg_response_times)
            overall_success = statistics.mean(success_rates)

            print(f"整体平均响应时间: {overall_avg:.2f}ms")
            print(f"整体成功率: {overall_success:.2f}%")

            # 性能评级
            if overall_avg < 100 and overall_success > 99:
                print("🎉 性能评级: 优秀")
            elif overall_avg < 200 and overall_success > 95:
                print("✅ 性能评级: 良好")
            elif overall_avg < 500 and overall_success > 90:
                print("⚠️ 性能评级: 一般")
            else:
                print("❌ 性能评级: 需要优化")

async def main():
    """主函数"""
    test_runner = PerformanceTest()

    try:
        await test_runner.setup_session()
        await test_runner.run_performance_tests()
        test_runner.print_performance_report()

        return True

    except Exception as e:
        logger.error(f"❌ 性能测试失败: {e}")
        return False

    finally:
        await test_runner.cleanup_session()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 性能测试被用户中断")
        sys.exit(1)