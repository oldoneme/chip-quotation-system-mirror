#!/usr/bin/env python3
"""
企业微信审批提供者 - 适配统一审批接口
遵循渐进式开发：最小可用版本，适配现有WeComApprovalService
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from .unified_approval_service import AbstractApprovalProvider, ApprovalResult, ApprovalMethod, ApprovalStatus
from .wecom_approval_service import WeComApprovalService


class WeComApprovalProvider(AbstractApprovalProvider):
    """企业微信审批提供者 - 适配器模式"""

    def __init__(self, db: Session):
        super().__init__(db)
        self._wecom_service = None
        self.logger = logging.getLogger(__name__)

    @property
    def wecom_service(self) -> WeComApprovalService:
        """延迟加载企业微信服务"""
        if self._wecom_service is None:
            self._wecom_service = WeComApprovalService(self.db)
        return self._wecom_service

    def is_available(self) -> bool:
        """检查企业微信审批是否可用"""
        try:
            # 简单的可用性检查：确保服务可以初始化
            service = self.wecom_service
            # 检查是否有必要的配置（模板ID等）
            return hasattr(service, 'quote_template_id') and bool(service.quote_template_id)
        except Exception as e:
            self.logger.warning(f"企业微信审批服务不可用: {e}")
            return False

    def submit_approval(self, quote_id: int, submitter_id: int) -> ApprovalResult:
        """提交审批到企业微信"""
        try:
            self.logger.info(f"提交报价单 {quote_id} 到企业微信审批，提交人: {submitter_id}")

            # 调用现有的企业微信服务
            sp_no = self.wecom_service.submit_quote_approval(quote_id, submitter_id)

            return ApprovalResult(
                success=True,
                message=f"已提交至企业微信审批，审批单号: {sp_no}",
                approval_method=ApprovalMethod.WECOM,
                new_status=ApprovalStatus.PENDING,
                approval_id=sp_no
            )
        except Exception as e:
            self.logger.error(f"提交企业微信审批失败: {e}")
            return ApprovalResult(
                success=False,
                message=f"提交企业微信审批失败: {str(e)}",
                approval_method=ApprovalMethod.WECOM,
                new_status=ApprovalStatus.NOT_SUBMITTED
            )

    def approve(self, quote_id: int, approver_id: int, comments: str = "") -> ApprovalResult:
        """批准审批 - 通过企业微信API"""
        try:
            self.logger.info(f"批准报价单 {quote_id}，批准人: {approver_id}")

            # 调用现有的企业微信审批服务
            result = self.wecom_service.approve_quote(quote_id, approver_id, comments)

            return ApprovalResult(
                success=True,
                message=f"报价单已通过企业微信批准",
                approval_method=ApprovalMethod.WECOM,
                new_status=ApprovalStatus.APPROVED,
                approval_id=result.get('sp_no') if isinstance(result, dict) else None
            )
        except Exception as e:
            self.logger.error(f"企业微信审批批准失败: {e}")
            return ApprovalResult(
                success=False,
                message=f"企业微信审批批准失败: {str(e)}",
                approval_method=ApprovalMethod.WECOM,
                new_status=ApprovalStatus.PENDING  # 保持原状态
            )

    def reject(self, quote_id: int, approver_id: int, reason: str = "") -> ApprovalResult:
        """拒绝审批 - 通过企业微信API"""
        try:
            self.logger.info(f"拒绝报价单 {quote_id}，批准人: {approver_id}")

            if not reason:
                reason = "未提供拒绝原因"

            # 调用现有的企业微信审批服务
            result = self.wecom_service.reject_quote(quote_id, approver_id, reason)

            return ApprovalResult(
                success=True,
                message=f"报价单已通过企业微信拒绝: {reason}",
                approval_method=ApprovalMethod.WECOM,
                new_status=ApprovalStatus.REJECTED,
                approval_id=result.get('sp_no') if isinstance(result, dict) else None
            )
        except Exception as e:
            self.logger.error(f"企业微信审批拒绝失败: {e}")
            return ApprovalResult(
                success=False,
                message=f"企业微信审批拒绝失败: {str(e)}",
                approval_method=ApprovalMethod.WECOM,
                new_status=ApprovalStatus.PENDING  # 保持原状态
            )