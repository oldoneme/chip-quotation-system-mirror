#!/usr/bin/env python3
"""
统一审批系统端到端测试
测试完整的审批流程：从提交到批准/拒绝的全流程
"""

import sys
import os
import asyncio
import aiohttp
import json
from datetime import datetime
import uuid

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API配置
BASE_URL = "http://127.0.0.1:8000"
API_V2_BASE = f"{BASE_URL}/api/v2/approval"

class UnifiedApprovalE2ETest:
    """统一审批系统端到端测试类"""

    def __init__(self):
        self.session = None
        self.test_quote_id = None
        self.test_results = []

    async def setup_session(self):
        """设置HTTP会话"""
        self.session = aiohttp.ClientSession()
        logger.info("HTTP会话已建立")

    async def cleanup_session(self):
        """清理HTTP会话"""
        if self.session:
            await self.session.close()
            logger.info("HTTP会话已关闭")

    def create_test_quote(self):
        """创建测试用的报价单"""
        try:
            with SessionLocal() as db:
                # 创建测试报价单
                quote_number = f"TEST-E2E-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                db.execute(text("""
                    INSERT INTO quotes (
                        quote_number, title, quote_type, customer_name,
                        currency, total_amount, status, approval_status,
                        approval_method, created_at, updated_at,
                        last_operation_channel, sync_required
                    ) VALUES (
                        :quote_number, :title, :quote_type, :customer_name,
                        :currency, :total_amount, :status, :approval_status,
                        :approval_method, :created_at, :updated_at,
                        :last_operation_channel, :sync_required
                    )
                """), {
                    'quote_number': quote_number,
                    'title': 'E2E测试报价单',
                    'quote_type': 'engineering',
                    'customer_name': '测试客户',
                    'currency': 'CNY',
                    'total_amount': 10000.0,
                    'status': 'draft',
                    'approval_status': 'not_submitted',
                    'approval_method': 'internal',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'last_operation_channel': 'INTERNAL',
                    'sync_required': False
                })

                # 获取新创建的报价单ID
                result = db.execute(text("SELECT id FROM quotes WHERE quote_number = :quote_number"),
                                  {'quote_number': quote_number})
                self.test_quote_id = result.scalar()

                db.commit()
                logger.info(f"✅ 创建测试报价单: {quote_number} (ID: {self.test_quote_id})")
                return quote_number

        except Exception as e:
            logger.error(f"❌ 创建测试报价单失败: {e}")
            raise

    def cleanup_test_quote(self):
        """清理测试报价单"""
        if not self.test_quote_id:
            return

        try:
            with SessionLocal() as db:
                # 删除审批记录
                db.execute(text("DELETE FROM approval_records WHERE quote_id = :quote_id"),
                          {'quote_id': self.test_quote_id})

                # 删除报价单
                db.execute(text("DELETE FROM quotes WHERE id = :quote_id"),
                          {'quote_id': self.test_quote_id})

                db.commit()
                logger.info(f"✅ 清理测试报价单 (ID: {self.test_quote_id})")

        except Exception as e:
            logger.error(f"❌ 清理测试报价单失败: {e}")

    async def test_api_health_check(self):
        """测试API健康检查"""
        test_name = "API健康检查"
        logger.info(f"开始测试: {test_name}")

        try:
            async with self.session.get(f"{API_V2_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ {test_name}: {data}")
                    self.test_results.append((test_name, True, f"API响应正常: {data}"))
                else:
                    error_msg = f"HTTP {response.status}"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    self.test_results.append((test_name, False, error_msg))

        except Exception as e:
            logger.error(f"❌ {test_name}: {e}")
            self.test_results.append((test_name, False, str(e)))

    async def test_get_approval_status(self):
        """测试获取审批状态"""
        test_name = "获取审批状态"
        logger.info(f"开始测试: {test_name}")

        try:
            async with self.session.get(f"{API_V2_BASE}/{self.test_quote_id}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ {test_name}: 状态 = {data.get('approval_status')}")
                    self.test_results.append((test_name, True, f"获取状态成功: {data.get('approval_status')}"))
                    return data
                else:
                    error_text = await response.text()
                    error_msg = f"HTTP {response.status}: {error_text}"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    self.test_results.append((test_name, False, error_msg))
                    return None

        except Exception as e:
            logger.error(f"❌ {test_name}: {e}")
            self.test_results.append((test_name, False, str(e)))
            return None

    async def test_submit_approval(self):
        """测试提交审批"""
        test_name = "提交审批"
        logger.info(f"开始测试: {test_name}")

        try:
            operation_data = {
                "action": "submit",
                "comments": "E2E测试提交审批",
                "channel": "auto"
            }

            async with self.session.post(
                f"{API_V2_BASE}/{self.test_quote_id}/operate",
                json=operation_data,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ {test_name}: 操作ID = {data.get('operation_id')}")
                    self.test_results.append((test_name, True, f"提交成功: {data.get('operation_id')}"))
                    return data
                else:
                    error_text = await response.text()
                    error_msg = f"HTTP {response.status}: {error_text}"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    self.test_results.append((test_name, False, error_msg))
                    return None

        except Exception as e:
            logger.error(f"❌ {test_name}: {e}")
            self.test_results.append((test_name, False, str(e)))
            return None

    async def test_approve_quote(self):
        """测试批准报价单"""
        test_name = "批准报价单"
        logger.info(f"开始测试: {test_name}")

        try:
            operation_data = {
                "action": "approve",
                "comments": "E2E测试批准报价单",
                "channel": "auto"
            }

            async with self.session.post(
                f"{API_V2_BASE}/{self.test_quote_id}/operate",
                json=operation_data,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ {test_name}: 操作ID = {data.get('operation_id')}")
                    self.test_results.append((test_name, True, f"批准成功: {data.get('operation_id')}"))
                    return data
                else:
                    error_text = await response.text()
                    error_msg = f"HTTP {response.status}: {error_text}"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    self.test_results.append((test_name, False, error_msg))
                    return None

        except Exception as e:
            logger.error(f"❌ {test_name}: {e}")
            self.test_results.append((test_name, False, str(e)))
            return None

    async def test_get_approval_list(self):
        """测试获取审批列表"""
        test_name = "获取审批列表"
        logger.info(f"开始测试: {test_name}")

        try:
            params = {
                "page": 1,
                "page_size": 10,
                "status": "approved"
            }

            async with self.session.get(f"{API_V2_BASE}/list", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    total = data.get('total', 0)
                    logger.info(f"✅ {test_name}: 获取到 {total} 条记录")
                    self.test_results.append((test_name, True, f"获取列表成功: {total} 条记录"))
                    return data
                else:
                    error_text = await response.text()
                    error_msg = f"HTTP {response.status}: {error_text}"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    self.test_results.append((test_name, False, error_msg))
                    return None

        except Exception as e:
            logger.error(f"❌ {test_name}: {e}")
            self.test_results.append((test_name, False, str(e)))
            return None

    def verify_database_consistency(self):
        """验证数据库一致性"""
        test_name = "数据库一致性验证"
        logger.info(f"开始测试: {test_name}")

        try:
            with SessionLocal() as db:
                # 检查报价单状态
                result = db.execute(text("""
                    SELECT approval_status, last_operation_channel, sync_required
                    FROM quotes WHERE id = :quote_id
                """), {'quote_id': self.test_quote_id})

                quote_data = result.fetchone()
                if not quote_data:
                    error_msg = "未找到测试报价单"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    self.test_results.append((test_name, False, error_msg))
                    return False

                approval_status = quote_data[0]
                operation_channel = quote_data[1]
                sync_required = quote_data[2]

                # 检查审批记录
                result = db.execute(text("""
                    SELECT COUNT(*), MAX(created_at)
                    FROM approval_records WHERE quote_id = :quote_id
                """), {'quote_id': self.test_quote_id})

                record_data = result.fetchone()
                record_count = record_data[0]
                last_record_time = record_data[1]

                logger.info(f"报价单状态: {approval_status}, 操作渠道: {operation_channel}")
                logger.info(f"审批记录数: {record_count}, 最后记录时间: {last_record_time}")

                # 验证一致性
                if approval_status == 'approved' and record_count >= 2:
                    logger.info(f"✅ {test_name}: 数据一致性正常")
                    self.test_results.append((test_name, True, "数据一致性验证通过"))
                    return True
                else:
                    error_msg = f"数据不一致: 状态={approval_status}, 记录数={record_count}"
                    logger.error(f"❌ {test_name}: {error_msg}")
                    self.test_results.append((test_name, False, error_msg))
                    return False

        except Exception as e:
            logger.error(f"❌ {test_name}: {e}")
            self.test_results.append((test_name, False, str(e)))
            return False

    async def run_complete_workflow(self):
        """运行完整的审批工作流"""
        logger.info("🚀 开始端到端测试完整审批工作流")

        try:
            # 1. API健康检查
            await self.test_api_health_check()

            # 2. 获取初始状态
            initial_status = await self.test_get_approval_status()

            # 3. 提交审批
            submit_result = await self.test_submit_approval()
            if submit_result:
                # 短暂等待状态更新
                await asyncio.sleep(1)

            # 4. 获取提交后状态
            after_submit_status = await self.test_get_approval_status()

            # 5. 批准报价单
            approve_result = await self.test_approve_quote()
            if approve_result:
                # 短暂等待状态更新
                await asyncio.sleep(1)

            # 6. 获取最终状态
            final_status = await self.test_get_approval_status()

            # 7. 获取审批列表
            await self.test_get_approval_list()

            # 8. 验证数据库一致性
            self.verify_database_consistency()

            logger.info("✅ 完整工作流测试完成")

        except Exception as e:
            logger.error(f"❌ 工作流测试失败: {e}")

    def print_test_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("📊 端到端测试结果汇总")
        print("=" * 60)

        passed_count = 0
        total_count = len(self.test_results)

        for test_name, passed, details in self.test_results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{test_name}: {status}")
            if details:
                print(f"   详情: {details}")

            if passed:
                passed_count += 1

        print("\n" + "-" * 60)
        print(f"总体结果: {passed_count}/{total_count} 通过")

        if passed_count == total_count:
            print("🎉 所有测试通过！统一审批系统运行正常！")
            return True
        else:
            print(f"⚠️ {total_count - passed_count} 个测试失败，需要检查")
            return False

async def main():
    """主函数"""
    test_runner = UnifiedApprovalE2ETest()

    try:
        print("🚀 开始统一审批系统端到端测试")
        print("=" * 60)

        # 设置
        await test_runner.setup_session()
        quote_number = test_runner.create_test_quote()

        # 运行测试
        await test_runner.run_complete_workflow()

        # 输出结果
        success = test_runner.print_test_results()

        return success

    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        return False

    finally:
        # 清理
        test_runner.cleanup_test_quote()
        await test_runner.cleanup_session()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)