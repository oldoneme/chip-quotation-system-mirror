import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....auth_routes import get_current_user
from ....database import get_db
from ....models import User
from ....schemas import ApprovalRecord, Quote as QuoteSchema
from ....services.quote_service import QuoteService
from .quote_endpoint_helpers import quote_to_schema, schedule_pdf_refresh
from .quote_route_helpers import ensure_admin_role, ensure_quote_access

router = APIRouter(prefix="/quotes", tags=["报价单审批"])


@router.post("/{quote_id}/submit", response_model=QuoteSchema)
async def submit_quote_for_approval(
    quote_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger = logging.getLogger("app.api.quotes")
    try:
        service = QuoteService(db)
        quote = service.submit_for_approval(quote_id, current_user.id)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        quote_detail = service.load_quote_with_details(quote.id) or quote
        schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            False,
            "snapshot_generation_failed_on_submit",
        )
        return quote_to_schema(service, quote_detail)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        logger.exception("submit_quote_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提交审批失败: {str(exc)}"
        )


@router.get("/{quote_id}/approval-records", response_model=list[ApprovalRecord])
async def get_quote_approval_records(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        service = QuoteService(db)
        ensure_quote_access(
            service.get_quote_by_id(quote_id),
            current_user,
            forbidden_detail="无权限访问此报价单的审批记录",
        )
        return service.get_approval_records(quote_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取审批记录失败: {str(e)}"
        )


@router.post("/{quote_id}/approve")
async def approve_quote(
    quote_id: str,
    approval_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        service = QuoteService(db)
        ensure_admin_role(current_user)
        quote = service.approve_quote(quote_id, current_user.id, approval_data.get('comments', '审批通过'))
        quote_detail = service.load_quote_with_details(quote.id) or quote
        schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            False,
            "snapshot_generation_failed_on_approve",
        )
        return {"message": "报价单已批准", "quote": quote_to_schema(service, quote_detail)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批准操作失败: {str(exc)}"
        )


@router.post("/{quote_id}/reject")
async def reject_quote(
    quote_id: str,
    rejection_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        service = QuoteService(db)
        ensure_admin_role(current_user)
        comments = rejection_data.get('comments', '')
        if not comments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="拒绝时必须提供拒绝原因"
            )
        quote = service.reject_quote(quote_id, current_user.id, comments)
        quote_detail = service.load_quote_with_details(quote.id) or quote
        schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            False,
            "snapshot_generation_failed_on_reject",
        )
        return {"message": "报价单已拒绝", "quote": quote_to_schema(service, quote_detail)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"拒绝操作失败: {str(exc)}"
        )
