#!/usr/bin/env python3
"""
调试审批操作
"""

import sys
import os
from datetime import datetime

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.approval_engine import (
    UnifiedApprovalEngine,
    ApprovalOperation,
    ApprovalAction,
    OperationChannel,
    ApprovalStatus
)
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_test_quote():
    """创建测试报价单"""
    with SessionLocal() as db:
        quote_number = f"DEBUG-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        db.execute(text("""
            INSERT INTO quotes (
                quote_number, title, quote_type, customer_name,
                currency, total_amount, status, approval_status,
                approval_method, created_by, created_at, updated_at,
                last_operation_channel, sync_required
            ) VALUES (
                :quote_number, :title, :quote_type, :customer_name,
                :currency, :total_amount, :status, :approval_status,
                :approval_method, :created_by, :created_at, :updated_at,
                :last_operation_channel, :sync_required
            )
        """), {
            'quote_number': quote_number,
            'title': '调试测试报价单',
            'quote_type': 'engineering',
            'customer_name': '测试客户',
            'currency': 'CNY',
            'total_amount': 5000.0,
            'status': 'draft',
            'approval_status': 'not_submitted',
            'approval_method': 'internal',
            'created_by': 1,  # 设置创建者ID
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_operation_channel': 'INTERNAL',
            'sync_required': False
        })

        # 获取新创建的报价单ID
        result = db.execute(text("SELECT id FROM quotes WHERE quote_number = :quote_number"),
                          {'quote_number': quote_number})
        quote_id = result.scalar()

        db.commit()
        logger.info(f"创建测试报价单: {quote_number} (ID: {quote_id})")
        return quote_id

def test_approval_operations(quote_id):
    """测试审批操作"""
    with SessionLocal() as db:
        try:
            # 初始化审批引擎
            engine = UnifiedApprovalEngine(db)
            logger.info("审批引擎初始化完成")

            # 测试1: 提交审批
            logger.info("=== 测试提交审批 ===")
            operation = ApprovalOperation(
                action=ApprovalAction.SUBMIT,
                quote_id=quote_id,
                operator_id=1,  # 假设用户ID为1
                channel=OperationChannel.INTERNAL,
                comments="调试测试提交"
            )

            result = engine.execute_operation(operation)
            logger.info(f"提交结果: {result}")

            if result.success:
                # 测试2: 批准
                logger.info("=== 测试批准操作 ===")
                operation = ApprovalOperation(
                    action=ApprovalAction.APPROVE,
                    quote_id=quote_id,
                    operator_id=1,
                    channel=OperationChannel.INTERNAL,
                    comments="调试测试批准"
                )

                result = engine.execute_operation(operation)
                logger.info(f"批准结果: {result}")

            # 检查最终状态
            logger.info("=== 检查最终状态 ===")
            result = db.execute(text("""
                SELECT approval_status, last_operation_channel, last_operation_id
                FROM quotes WHERE id = :quote_id
            """), {'quote_id': quote_id})

            quote_data = result.fetchone()
            logger.info(f"报价单最终状态: {quote_data}")

            # 检查审批记录
            result = db.execute(text("""
                SELECT action, status, operation_id, created_at
                FROM approval_records WHERE quote_id = :quote_id
                ORDER BY created_at
            """), {'quote_id': quote_id})

            records = result.fetchall()
            logger.info(f"审批记录数量: {len(records)}")
            for record in records:
                logger.info(f"记录: {record}")

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)

def cleanup_test_quote(quote_id):
    """清理测试报价单"""
    with SessionLocal() as db:
        try:
            db.execute(text("DELETE FROM approval_records WHERE quote_id = :quote_id"),
                      {'quote_id': quote_id})
            db.execute(text("DELETE FROM quotes WHERE id = :quote_id"),
                      {'quote_id': quote_id})
            db.commit()
            logger.info(f"清理测试报价单: {quote_id}")
        except Exception as e:
            logger.error(f"清理失败: {e}")

def main():
    """主函数"""
    logger.info("开始调试审批操作")

    # 创建测试数据
    quote_id = create_test_quote()

    try:
        # 测试操作
        test_approval_operations(quote_id)
    finally:
        # 清理
        cleanup_test_quote(quote_id)

    logger.info("调试完成")

if __name__ == "__main__":
    main()