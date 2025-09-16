#!/usr/bin/env python3
"""
内部审批提供者 - 最小可用版本
遵循渐进式开发，先实现基本功能
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from .unified_approval_service import (
    AbstractApprovalProvider, ApprovalResult, ApprovalMethod, ApprovalStatus
)
from ..models import Quote

logger = logging.getLogger(__name__)

class InternalApprovalProvider(AbstractApprovalProvider):
    """内部审批提供者 - 最小版本"""

    def __init__(self, db: Session):
        super().__init__(db)

    def is_available(self) -> bool:
        """内部审批始终可用"""
        return True

    def submit_approval(self, quote_id: int, submitter_id: int) -> ApprovalResult:
        """提交到内部审批 - 基础版本"""
        try:
            logger.info(f"内部审批提交: quote_id={quote_id}, submitter_id={submitter_id}")

            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                return ApprovalResult(
                    success=False,
                    message=f"报价单 {quote_id} 不存在",
                    approval_method=ApprovalMethod.INTERNAL,
                    new_status=ApprovalStatus.NOT_SUBMITTED
                )

            # 简单更新提交信息
            quote.submitted_at = datetime.utcnow()
            quote.submitted_by = submitter_id
            self.db.commit()

            return ApprovalResult(
                success=True,
                message="成功提交到内部审批",
                approval_method=ApprovalMethod.INTERNAL,
                new_status=ApprovalStatus.PENDING
            )

        except Exception as e:
            logger.error(f"内部审批提交失败: {str(e)}")
            return ApprovalResult(
                success=False,
                message=f"提交失败: {str(e)}",
                approval_method=ApprovalMethod.INTERNAL,
                new_status=ApprovalStatus.NOT_SUBMITTED
            )

    def approve(self, quote_id: int, approver_id: int, comments: str = "") -> ApprovalResult:
        """批准 - 基础版本"""
        try:
            logger.info(f"内部审批批准: quote_id={quote_id}, approver_id={approver_id}")

            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                raise ValueError(f"报价单 {quote_id} 不存在")

            # 基础批准逻辑
            self.db.commit()

            return ApprovalResult(
                success=True,
                message="内部审批批准成功",
                approval_method=ApprovalMethod.INTERNAL,
                new_status=ApprovalStatus.APPROVED
            )

        except Exception as e:
            logger.error(f"内部审批批准失败: {str(e)}")
            raise

    def reject(self, quote_id: int, approver_id: int, reason: str = "") -> ApprovalResult:
        """拒绝 - 基础版本"""
        try:
            logger.info(f"内部审批拒绝: quote_id={quote_id}, approver_id={approver_id}")

            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                raise ValueError(f"报价单 {quote_id} 不存在")

            # 基础拒绝逻辑
            self.db.commit()

            return ApprovalResult(
                success=True,
                message="内部审批拒绝成功",
                approval_method=ApprovalMethod.INTERNAL,
                new_status=ApprovalStatus.REJECTED
            )

        except Exception as e:
            logger.error(f"内部审批拒绝失败: {str(e)}")
            raise