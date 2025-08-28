#!/usr/bin/env python3
"""
报价单导出API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ....database import get_db
from ....services.export_service import ExportService
from ....services.simple_export_service import SimpleExportService
from ....auth import get_current_user
from ....models import User

router = APIRouter(prefix="/export", tags=["导出功能"])


@router.get("/quote/{quote_id}/pdf")
async def export_quote_pdf(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单为PDF格式
    """
    try:
        service = ExportService(db)
        return service.export_quote_pdf(quote_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{quote_id}/excel")
async def export_quote_excel(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单为Excel格式
    """
    try:
        service = ExportService(db)
        return service.export_quote_excel(quote_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes/summary/excel")
async def export_quotes_summary_excel(
    quote_ids: Optional[str] = Query(None, description="报价单ID列表，用逗号分隔"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单汇总表（Excel格式）
    """
    try:
        service = ExportService(db)
        
        # 解析报价单ID列表
        parsed_quote_ids = None
        if quote_ids:
            try:
                parsed_quote_ids = [int(x.strip()) for x in quote_ids.split(',') if x.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="报价单ID格式错误")
        
        return service.export_quotes_summary_excel(
            quote_ids=parsed_quote_ids,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/quote-pdf")
async def get_quote_pdf_template_info():
    """
    获取PDF模板信息和自定义选项
    """
    return {
        "template_info": {
            "formats": ["A4", "Letter"],
            "orientations": ["portrait", "landscape"],
            "languages": ["zh_CN", "en_US"],
            "themes": ["default", "minimal", "corporate"]
        },
        "customization": {
            "logo_supported": True,
            "header_footer": True,
            "watermark": True,
            "color_scheme": True
        }
    }


@router.get("/templates/quote-excel")  
async def get_quote_excel_template_info():
    """
    获取Excel模板信息和自定义选项
    """
    return {
        "template_info": {
            "sheets": ["基本信息", "报价明细", "金额汇总"],
            "formats": ["xlsx", "xls"],
            "chart_support": True
        },
        "customization": {
            "conditional_formatting": True,
            "pivot_tables": True,
            "charts": True,
            "formulas": True
        }
    }


@router.get("/quote/{quote_id}/json")
async def export_quote_json(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单为JSON格式（无依赖）
    """
    try:
        service = SimpleExportService(db)
        return service.export_quote_json(quote_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{quote_id}/csv")
async def export_quote_csv(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单为CSV格式（无依赖）
    """
    try:
        service = SimpleExportService(db)
        return service.export_quote_csv(quote_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{quote_id}/html")
async def export_quote_html(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单为HTML格式（无依赖）
    """
    try:
        service = SimpleExportService(db)
        return service.export_quote_html(quote_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes/summary/csv")
async def export_quotes_summary_csv(
    quote_ids: Optional[str] = Query(None, description="报价单ID列表，用逗号分隔"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单汇总表（CSV格式，无依赖）
    """
    try:
        service = SimpleExportService(db)
        
        # 解析报价单ID列表
        parsed_quote_ids = None
        if quote_ids:
            try:
                parsed_quote_ids = [int(x.strip()) for x in quote_ids.split(',') if x.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="报价单ID格式错误")
        
        return service.export_quotes_summary_csv(
            quote_ids=parsed_quote_ids,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))