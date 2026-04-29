from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ....models import User, Quote as QuoteModel


def ensure_quote_access(
    quote: Optional[QuoteModel],
    current_user: User,
    *,
    forbidden_detail: str = "无权限访问此报价单",
) -> QuoteModel:
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报价单不存在",
        )

    is_owner = quote.created_by == current_user.id
    is_super_admin = current_user.role == "super_admin"
    is_current_approver = (
        current_user.role in ["manager", "admin"]
        and quote.current_approver_id == current_user.id
        and quote.approval_status in ["pending", "approved", "rejected"]
    )
    is_admin_reviewer = (
        current_user.role == "admin"
        and quote.approval_status in ["approved", "rejected"]
    )

    if not (is_owner or is_super_admin or is_current_approver or is_admin_reviewer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=forbidden_detail,
        )

    return quote


def get_quote_by_identifier(service, quote_identifier: str):
    if quote_identifier.isdigit():
        return service.get_quote_by_id(int(quote_identifier))

    from uuid import UUID
    try:
        UUID(quote_identifier)
        return service.get_quote_by_approval_token(quote_identifier)
    except (ValueError, AttributeError):
        pass

    return service.get_quote_by_number(quote_identifier)


def load_quote_with_pdf_relations(db: Session, quote_identifier: str) -> Optional[QuoteModel]:
    base_query = db.query(QuoteModel).options(
        selectinload(QuoteModel.items),
        selectinload(QuoteModel.creator),
        selectinload(QuoteModel.pdf_cache),
    )

    if quote_identifier.isdigit():
        return base_query.filter(QuoteModel.id == int(quote_identifier), QuoteModel.is_deleted == False).first()

    from uuid import UUID

    try:
        UUID(quote_identifier)
        return base_query.filter(QuoteModel.approval_link_token == quote_identifier, QuoteModel.is_deleted == False).first()
    except (ValueError, AttributeError):
        return base_query.filter(QuoteModel.quote_number == quote_identifier, QuoteModel.is_deleted == False).first()


def ensure_admin_role(current_user: User) -> None:
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行审批操作",
        )


def queue_export_task(quote_id: str, export_format: str) -> dict:
    from ....services.outbox import outbox

    outbox.add("generate_export", {"quote_id": quote_id, "format": export_format})
    return {
        "message": f"{export_format.upper()}导出任务已创建",
        "quote_id": quote_id,
        "format": export_format,
        "status": "processing",
    }
