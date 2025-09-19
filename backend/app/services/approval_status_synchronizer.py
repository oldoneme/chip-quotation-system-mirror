#!/usr/bin/env python3
"""
审批状态同步器 - 解决status和approval_status字段冲突
遵循渐进式开发：最小可用版本，统一状态管理
"""

import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from enum import Enum

from ..models import Quote
from .unified_approval_service import ApprovalMethod

# 使用和 approval_engine 相同的 ApprovalStatus 定义以确保一致性
class ApprovalStatus(Enum):
    """审批状态枚举 - 与 approval_engine 保持一致"""
    NOT_SUBMITTED = "not_submitted"    # 未提交
    DRAFT = "draft"                    # 草稿
    PENDING = "pending"                # 待审批
    APPROVED = "approved"              # 已批准
    REJECTED = "rejected"              # 已拒绝
    WITHDRAWN = "withdrawn"            # 已撤回


class QuoteStatus(Enum):
    """报价单主要状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    FORWARDED = "forwarded"


class ApprovalStatusSynchronizer:
    """审批状态同步器 - 保持双状态字段一致性"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def map_approval_to_quote_status(approval_status) -> QuoteStatus:
        """将统一审批状态映射到报价单状态 - 使用字符串值进行匹配以避免enum类型不匹配"""
        # 使用字符串值进行映射，避免不同 ApprovalStatus 枚举类的比较问题
        status_value = approval_status.value if hasattr(approval_status, 'value') else str(approval_status)

        value_mapping = {
            "not_submitted": QuoteStatus.DRAFT,
            "pending": QuoteStatus.PENDING,
            "approved": QuoteStatus.APPROVED,
            "rejected": QuoteStatus.REJECTED,
        }
        return value_mapping.get(status_value, QuoteStatus.DRAFT)

    @staticmethod
    def map_quote_to_approval_status(quote_status: QuoteStatus) -> ApprovalStatus:
        """将报价单状态映射到审批状态"""
        mapping = {
            QuoteStatus.DRAFT: ApprovalStatus.NOT_SUBMITTED,
            QuoteStatus.PENDING: ApprovalStatus.PENDING,
            QuoteStatus.APPROVED: ApprovalStatus.APPROVED,
            QuoteStatus.REJECTED: ApprovalStatus.REJECTED,
            QuoteStatus.RETURNED: ApprovalStatus.PENDING,  # 退回视为等待修改
            QuoteStatus.FORWARDED: ApprovalStatus.PENDING,  # 转发视为审批中
        }
        return mapping.get(quote_status, ApprovalStatus.NOT_SUBMITTED)

    def sync_status_fields(self, quote_id: int, new_approval_status: ApprovalStatus) -> bool:
        """同步报价单的双状态字段"""
        try:
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                self.logger.error(f"报价单 {quote_id} 不存在")
                return False

            # 记录原始状态
            old_status = quote.status
            old_approval_status = quote.approval_status

            # 更新双状态字段
            new_quote_status = self.map_approval_to_quote_status(new_approval_status)


            quote.status = new_quote_status.value
            quote.approval_status = new_approval_status.value

            self.db.commit()

            self.logger.info(
                f"报价单 {quote_id} 状态同步完成: "
                f"status: {old_status} -> {new_quote_status.value}, "
                f"approval_status: {old_approval_status} -> {new_approval_status.value}"
            )

            return True

        except Exception as e:
            self.logger.error(f"状态同步失败 - 报价单 {quote_id}: {e}")
            self.db.rollback()
            return False

    def check_status_consistency(self, quote_id: int) -> Tuple[bool, str]:
        """检查状态字段一致性"""
        try:
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                return False, f"报价单 {quote_id} 不存在"

            # 检查状态映射一致性
            try:
                quote_status_enum = QuoteStatus(quote.status)
                approval_status_enum = ApprovalStatus(quote.approval_status)
            except ValueError as e:
                return False, f"状态值无效: {e}"

            # 检查映射一致性
            expected_approval = self.map_quote_to_approval_status(quote_status_enum)
            expected_quote = self.map_approval_to_quote_status(approval_status_enum)

            if (expected_approval == approval_status_enum and
                expected_quote == quote_status_enum):
                return True, "状态一致"
            else:
                return False, (
                    f"状态不一致 - status: {quote.status}, "
                    f"approval_status: {quote.approval_status}, "
                    f"期望映射: {expected_approval.value} / {expected_quote.value}"
                )

        except Exception as e:
            return False, f"一致性检查失败: {e}"

    def repair_inconsistent_status(self, quote_id: int, primary_field: str = "approval_status") -> bool:
        """修复不一致的状态（以某个字段为准）"""
        try:
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                self.logger.error(f"报价单 {quote_id} 不存在")
                return False

            if primary_field == "approval_status":
                # 以approval_status为准，更新status
                approval_status_enum = ApprovalStatus(quote.approval_status)
                new_quote_status = self.map_approval_to_quote_status(approval_status_enum)
                quote.status = new_quote_status.value

                self.logger.info(f"以approval_status为准修复报价单 {quote_id}: status -> {new_quote_status.value}")
            else:
                # 以status为准，更新approval_status
                quote_status_enum = QuoteStatus(quote.status)
                new_approval_status = self.map_quote_to_approval_status(quote_status_enum)
                quote.approval_status = new_approval_status.value

                self.logger.info(f"以status为准修复报价单 {quote_id}: approval_status -> {new_approval_status.value}")

            self.db.commit()
            return True

        except Exception as e:
            self.logger.error(f"状态修复失败 - 报价单 {quote_id}: {e}")
            self.db.rollback()
            return False

    def batch_check_consistency(self) -> dict:
        """批量检查所有报价单的状态一致性"""
        try:
            quotes = self.db.query(Quote).all()
            results = {
                "total": len(quotes),
                "consistent": 0,
                "inconsistent": 0,
                "errors": []
            }

            for quote in quotes:
                is_consistent, message = self.check_status_consistency(quote.id)
                if is_consistent:
                    results["consistent"] += 1
                else:
                    results["inconsistent"] += 1
                    results["errors"].append({
                        "quote_id": quote.id,
                        "quote_number": quote.quote_number,
                        "message": message
                    })

            self.logger.info(
                f"批量一致性检查完成: 总计 {results['total']}, "
                f"一致 {results['consistent']}, 不一致 {results['inconsistent']}"
            )

            return results

        except Exception as e:
            self.logger.error(f"批量一致性检查失败: {e}")
            return {"error": str(e)}