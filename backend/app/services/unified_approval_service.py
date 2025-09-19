#!/usr/bin/env python3
"""
统一审批服务 - 最小可用版本
遵循渐进式开发，先实现核心抽象接口
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session

# 审批方法枚举 - 最小版本
class ApprovalMethod(Enum):
    INTERNAL = "internal"    # 内部审批
    WECOM = "wecom"         # 企业微信审批

# 审批状态枚举 - 最小版本
class ApprovalStatus(Enum):
    NOT_SUBMITTED = "not_submitted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# 审批结果 - 最小版本
@dataclass
class ApprovalResult:
    success: bool
    message: str
    approval_method: ApprovalMethod
    new_status: ApprovalStatus
    approval_id: Optional[str] = None

# 抽象审批提供者 - 只包含核心方法
class AbstractApprovalProvider(ABC):
    """审批提供者抽象基类 - 最小版本"""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def submit_approval(self, quote_id: int, submitter_id: int) -> ApprovalResult:
        """提交审批"""
        pass

    @abstractmethod
    def approve(self, quote_id: int, approver_id: int, comments: str = "") -> ApprovalResult:
        """批准"""
        pass

    @abstractmethod
    def reject(self, quote_id: int, approver_id: int, reason: str = "") -> ApprovalResult:
        """拒绝"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查提供者是否可用"""
        pass


# 简单统一审批服务 - 最小版本
class UnifiedApprovalService:
    """统一审批服务 - 基础路由功能"""

    def __init__(self, db: Session):
        self.db = db
        # 延迟加载提供者
        self._internal_provider = None
        self._wecom_provider = None

    @property
    def internal_provider(self):
        """延迟加载内部审批提供者"""
        if self._internal_provider is None:
            from .internal_approval_provider import InternalApprovalProvider
            self._internal_provider = InternalApprovalProvider(self.db)
        return self._internal_provider

    @property
    def wecom_provider(self):
        """延迟加载企业微信审批提供者"""
        if self._wecom_provider is None:
            from .wecom_approval_provider import WeComApprovalProvider
            self._wecom_provider = WeComApprovalProvider(self.db)
        return self._wecom_provider

    def select_provider(self, quote_id: int) -> AbstractApprovalProvider:
        """选择审批提供者 - 智能选择版本"""
        # 优先尝试企业微信审批，如果不可用则回退到内部审批
        if self.wecom_provider.is_available():
            return self.wecom_provider
        else:
            # 回退到内部审批
            return self.internal_provider

    def submit_approval(self, quote_id: int, submitter_id: int) -> ApprovalResult:
        """统一提交审批入口 - 使用新的统一审批引擎"""
        try:
            # 使用新的统一审批引擎
            from .approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

            engine = UnifiedApprovalEngine(self.db)
            operation = ApprovalOperation(
                action=ApprovalAction.SUBMIT,
                quote_id=quote_id,
                operator_id=submitter_id,
                channel=OperationChannel.INTERNAL,  # V1 API调用视为内部操作
                comments="通过V1 API提交"
            )

            result = engine.execute_operation(operation)

            # 转换为旧的结果格式以保持向后兼容
            return ApprovalResult(
                success=result.success,
                message=result.message,
                approval_method=result.approval_method,
                new_status=ApprovalStatus(result.new_status.value),
                approval_id=getattr(result, 'operation_id', None)
            )
        except Exception as e:
            # 回退到旧实现
            provider = self.select_provider(quote_id)
            return provider.submit_approval(quote_id, submitter_id)

    def approve(self, quote_id: int, approver_id: int, comments: str = "") -> ApprovalResult:
        """统一批准入口 - 使用新的统一审批引擎"""
        try:
            # 使用新的统一审批引擎
            from .approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

            engine = UnifiedApprovalEngine(self.db)
            operation = ApprovalOperation(
                action=ApprovalAction.APPROVE,
                quote_id=quote_id,
                operator_id=approver_id,
                channel=OperationChannel.INTERNAL,
                comments=comments or "通过V1 API批准"
            )

            result = engine.execute_operation(operation)

            # 转换为旧的结果格式以保持向后兼容
            return ApprovalResult(
                success=result.success,
                message=result.message,
                approval_method=result.approval_method,
                new_status=ApprovalStatus(result.new_status.value),
                approval_id=getattr(result, 'operation_id', None)
            )
        except Exception as e:
            # 回退到旧实现
            provider = self.select_provider(quote_id)
            return provider.approve(quote_id, approver_id, comments)

    def reject(self, quote_id: int, approver_id: int, reason: str = "") -> ApprovalResult:
        """统一拒绝入口 - 使用新的统一审批引擎"""
        try:
            # 使用新的统一审批引擎
            from .approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

            engine = UnifiedApprovalEngine(self.db)
            operation = ApprovalOperation(
                action=ApprovalAction.REJECT,
                quote_id=quote_id,
                operator_id=approver_id,
                channel=OperationChannel.INTERNAL,
                reason=reason or "通过V1 API拒绝",
                comments=reason
            )

            result = engine.execute_operation(operation)

            # 转换为旧的结果格式以保持向后兼容
            return ApprovalResult(
                success=result.success,
                message=result.message,
                approval_method=result.approval_method,
                new_status=ApprovalStatus(result.new_status.value),
                approval_id=getattr(result, 'operation_id', None)
            )
        except Exception as e:
            # 回退到旧实现
            provider = self.select_provider(quote_id)
            return provider.reject(quote_id, approver_id, reason)