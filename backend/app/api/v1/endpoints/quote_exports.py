from typing import Optional
import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from ....auth_routes import get_current_user_strict_multi_source
from ....database import get_db
from ....models import User
from ....services.quote_service import QuoteService, PDFGenerationInProgress
from .quote_route_helpers import ensure_quote_access, get_quote_by_identifier, load_quote_with_pdf_relations, queue_export_task

router = APIRouter(prefix="/quotes", tags=["报价单导出"])


@router.get("/{quote_id}/export/pdf")
async def export_quote_pdf(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict_multi_source)
):
    """导出报价单PDF - 占位实现"""
    try:
        service = QuoteService(db)
        ensure_quote_access(
            get_quote_by_identifier(service, quote_id),
            current_user,
            forbidden_detail="无权限导出此报价单",
        )
        return queue_export_task(quote_id, "pdf")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF导出失败: {str(e)}"
        )


@router.get("/{quote_id}/export/excel")
async def export_quote_excel(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict_multi_source)
):
    """导出报价单Excel - 占位实现"""
    try:
        service = QuoteService(db)
        ensure_quote_access(
            get_quote_by_identifier(service, quote_id),
            current_user,
            forbidden_detail="无权限导出此报价单",
        )
        return queue_export_task(quote_id, "excel")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel导出失败: {str(e)}"
        )


@router.get("/{quote_id}/pdf")
async def get_quote_pdf(
    quote_id: str,
    download: bool = Query(False, description="是否下载文件"),
    columns: Optional[str] = Query(None, description="前端列配置JSON"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_strict_multi_source)
):
    """获取报价单PDF，优先使用前端快照缓存，必要时兜底WeasyPrint"""
    logger = logging.getLogger("app.api.quotes")
    try:
        column_configs = None
        if columns:
            try:
                column_configs = json.loads(columns)
            except json.JSONDecodeError:
                logger.warning("invalid_column_config", extra={"quote_identifier": quote_id})

        quote = ensure_quote_access(load_quote_with_pdf_relations(db, quote_id), current_user)

        service = QuoteService(db)
        try:
            cache = await asyncio.to_thread(
                service.ensure_pdf_cache, quote, current_user, False, column_configs, True, False
            )
        except PDFGenerationInProgress:
            logger.info("PDF正在生成中，返回202状态码", extra={"quote_id": quote_id, "quote_number": quote.quote_number})
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "status": "generating",
                    "message": "PDF正在生成中，请稍后再试"
                }
            )

        pdf_path = Path(cache.pdf_path)
        if not pdf_path.is_absolute():
            pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.info("PDF文件未就绪，返回202状态码", extra={"quote_id": quote_id, "quote_number": quote.quote_number})
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "status": "generating",
                    "message": "PDF正在生成中，请稍后再试"
                }
            )

        filename = f"{quote.quote_number}_quote.pdf"
        disposition = "attachment" if download else "inline"
        from urllib.parse import quote as url_quote
        encoded = url_quote(f"{quote.quote_number}_报价单.pdf")
        headers = {
            "Content-Disposition": f"{disposition}; filename=\"{filename}\"; filename*=UTF-8''{encoded}",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=filename,
            headers=headers,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("get_quote_pdf_failed", extra={"error": str(exc), "quote_id": quote_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF生成失败: {str(exc)}"
        )
