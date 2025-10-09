"""
报价单相关的API端点
"""

from typing import List, Optional
import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from ....auth import get_current_user
from ....database import get_db, SessionLocal
from ....models import User, Quote as QuoteModel
from ....schemas import (
    Quote as QuoteSchema,
    QuoteCreate,
    QuoteUpdate,
    QuoteList,
    QuoteFilter,
    QuoteStatusUpdate,
    QuoteStatistics,
    ApprovalRecord,
)
from ....services.quote_service import QuoteService, PDFGenerationInProgress

router = APIRouter(prefix="/quotes", tags=["报价单管理"])


def _quote_to_schema(service: QuoteService, quote: QuoteModel) -> QuoteSchema:
    """将 SQLAlchemy Quote 实例转换为带 pdf_url 的响应模型"""
    pdf_url = service.get_pdf_url(quote)
    model = QuoteSchema.model_validate(quote, from_attributes=True)
    if pdf_url:
        model = model.model_copy(update={"pdf_url": pdf_url})
    return model



def _generate_pdf_cache_background(
    quote_id: int,
    user_id: int,
    force: bool,
    event: str,
    column_configs: Optional[dict] = None,
) -> None:
    session = SessionLocal()
    try:
        service = QuoteService(session)
        quote = service.load_quote_with_details(quote_id)
        user = session.query(User).filter(User.id == user_id).first()
        if not quote or not user:
            return
        try:
            service.ensure_pdf_cache(
                quote, user, force=force, column_configs=column_configs
            )
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("app.snapshot").error(
                json.dumps(
                    {
                        "event": event,
                        "quote_id": quote.id,
                        "quote_number": quote.quote_number,
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
    finally:
        session.close()


def _schedule_pdf_refresh(
    background_tasks: BackgroundTasks,
    quote_id: int,
    user_id: int,
    force: bool,
    event: str,
    column_configs: Optional[dict] = None,
) -> None:
    if background_tasks is None:
        return
    background_tasks.add_task(
        _generate_pdf_cache_background,
        quote_id,
        user_id,
        force,
        event,
        column_configs,
    )


def _list_item_to_dict(service: QuoteService, quote: QuoteModel) -> dict:
    model = QuoteList.model_validate(quote, from_attributes=True)
    pdf_url = service.get_pdf_url(quote)
    if pdf_url:
        model = model.model_copy(update={"pdf_url": pdf_url})
    return model.model_dump(mode="json")




@router.post("/", response_model=QuoteSchema, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新报价单并生成快照PDF缓存"""
    logger = logging.getLogger("app.api.quotes")
    try:
        service = QuoteService(db)
        quote = service.create_quote(quote_data, current_user.id)
        quote_detail = service.load_quote_with_details(quote.id) or quote
        _schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            True,
            "snapshot_generation_failed_on_create",
        )
        return _quote_to_schema(service, quote_detail)
    except Exception as exc:  # pragma: no cover - 捕获意外错误并转译
        logger.exception("create_quote_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建报价单失败: {str(exc)}"
        )



@router.get("/", response_model=dict)
async def get_quotes(
    status: Optional[str] = Query(None, description="状态筛选"),
    quote_type: Optional[str] = Query(None, description="报价类型筛选"),
    customer_name: Optional[str] = Query(None, description="客户名称筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报价单列表并附带PDF缓存链接"""
    logger = logging.getLogger("app.api.quotes")
    try:
        service = QuoteService(db)
        filter_params = QuoteFilter(
            status=status,
            quote_type=quote_type,
            customer_name=customer_name,
            page=page,
            size=size
        )

        quotes, total = service.get_quotes(filter_params, current_user.id if current_user else None)
        items = [_list_item_to_dict(service, q) for q in quotes]

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }
    except Exception as exc:  # pragma: no cover - 捕获意外错误
        logger.exception("get_quotes_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报价单列表失败: {str(exc)}"
        )



@router.get("/test", response_model=dict)
async def get_quotes_test(
    db: Session = Depends(get_db)
):
    """测试端点 - 直接返回报价单列表"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy import desc
        from sqlalchemy.orm import selectinload
        
        # 获取所有未删除的报价单，按创建时间倒序排列，并关联用户信息和报价项目
        quotes = db.query(Quote).filter(Quote.is_deleted == False).options(
            selectinload(Quote.items)
        ).join(User, Quote.created_by == User.id, isouter=True).order_by(desc(Quote.created_at)).all()
        
        result = []
        for quote in quotes:
            # 获取创建者姓名
            creator_name = "未知"
            if quote.creator:
                creator_name = quote.creator.name
            
            # 格式化报价明细
            quote_details = []
            for item in quote.items:
                # 从configuration中解析UPH和计算机时费率
                uph = None
                hourly_rate = None
                if item.configuration:
                    import re
                    uph_match = re.search(r'UPH:(\d+)', item.configuration)
                    if uph_match:
                        uph = int(uph_match.group(1))
                        hourly_rate = f"¥{(item.unit_price * uph):.2f}/小时" if item.unit_price else "¥0.00/小时"
                
                detail = {
                    "item_name": item.item_name,
                    "item_description": item.item_description,
                    "machine_type": item.machine_type,
                    "machine_model": item.machine_model,
                    "configuration": item.configuration,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "total_price": item.total_price,
                    "uph": uph,
                    "hourly_rate": hourly_rate
                }
                quote_details.append(detail)
            
            result.append({
                "id": quote.id,
                "quote_number": quote.quote_number,
                "title": quote.title,
                "quote_type": quote.quote_type,
                "customer_name": quote.customer_name,
                "status": quote.status,
                "approval_status": quote.approval_status,  # 添加审批状态字段
                "created_at": quote.created_at.isoformat(),
                "total_amount": quote.total_amount,
                "creator_name": creator_name,
                "quote_details": quote_details
            })
        return {
            "items": result,
            "total": len(result),
            "page": 1,
            "size": len(result)
        }
    except Exception as e:
        print(f"测试端点错误: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.get("/by-uuid/{quote_uuid}")
async def get_quote_by_uuid(
    quote_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    按UUID查询报价单详情（完整数据）
    用于企业微信审批链接访问
    """
    # 直接调用已存在的detail/by-id接口的逻辑
    return await get_quote_detail_by_id(quote_uuid, db)


@router.get("/detail/by-id/{quote_id}")
async def get_quote_detail_by_id(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """按ID获取报价单详情（包含创建者姓名）"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy.orm import selectinload
        
        # 获取报价单详情，关联用户和明细项
        quote = (db.query(Quote)
                .options(selectinload(Quote.items), selectinload(Quote.creator))
                .filter(Quote.id == quote_id)
                .first())
        
        if not quote:
            return {"error": "报价单不存在"}
        
        # 获取创建者姓名
        creator_name = "未知"
        if quote.creator:
            creator_name = quote.creator.name
        
        # 格式化报价明细
        quote_items = []
        for item in quote.items:
            # 从configuration中解析UPH和计算机时费率
            uph = None
            hourly_rate = None
            if item.configuration:
                import re
                uph_match = re.search(r'UPH:(\d+)', item.configuration)
                if uph_match:
                    uph = int(uph_match.group(1))
                    hourly_rate = f"¥{(item.unit_price * uph):.2f}/小时" if item.unit_price else "¥0.00/小时"
            
            quote_items.append({
                "id": item.id,
                "item_name": item.item_name,
                "item_description": item.item_description,
                "machine_type": item.machine_type,
                "supplier": item.supplier,
                "machine_model": item.machine_model,
                "configuration": item.configuration,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "machine_id": item.machine_id,
                "configuration_id": item.configuration_id,
                "uph": uph,
                "hourly_rate": hourly_rate
            })
        
        return {
            "id": quote.id,
            "quote_number": quote.quote_number,
            "title": quote.title,
            "quote_type": quote.quote_type,
            "customer_name": quote.customer_name,
            "customer_contact": quote.customer_contact,
            "customer_phone": quote.customer_phone,
            "customer_email": quote.customer_email,
            "customer_address": quote.customer_address,
            "quote_unit": quote.quote_unit,  # 添加报价单位字段
            "currency": quote.currency,
            "subtotal": quote.subtotal,
            "discount": quote.discount,
            "tax_rate": quote.tax_rate,
            "tax_amount": quote.tax_amount,
            "total_amount": quote.total_amount,
            "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
            "payment_terms": quote.payment_terms,
            "description": quote.description,
            "notes": quote.notes,
            "status": quote.status,
            "approval_status": quote.approval_status,  # 添加审批状态字段
            "version": quote.version,
            "submitted_at": quote.submitted_at.isoformat() if quote.submitted_at else None,
            "approved_at": quote.approved_at.isoformat() if quote.approved_at else None,
            "approved_by": quote.approved_by,
            "rejection_reason": quote.rejection_reason,
            "wecom_approval_id": quote.wecom_approval_id,
            "created_by": quote.created_by,
            "creator_name": creator_name,
            "created_at": quote.created_at.isoformat() if quote.created_at else None,
            "updated_at": quote.updated_at.isoformat() if quote.updated_at else None,
            "items": quote_items
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.get("/detail/{quote_number}")
async def get_quote_detail_test(
    quote_number: str,
    db: Session = Depends(get_db)
):
    """测试端点 - 获取报价单详情（包含创建者姓名）"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy.orm import selectinload
        
        # 获取报价单详情，关联用户和明细项
        quote = (db.query(Quote)
                .options(selectinload(Quote.items), selectinload(Quote.creator))
                .filter(Quote.quote_number == quote_number)
                .first())
        
        if not quote:
            return {"error": "报价单不存在"}
        
        # 获取创建者姓名
        creator_name = "未知"
        if quote.creator:
            creator_name = quote.creator.name
        
        # 格式化报价明细
        quote_items = []
        for item in quote.items:
            # 从configuration中解析UPH和计算机时费率
            uph = None
            hourly_rate = None
            if item.configuration:
                import re
                uph_match = re.search(r'UPH:(\d+)', item.configuration)
                if uph_match:
                    uph = int(uph_match.group(1))
                    hourly_rate = f"¥{(item.unit_price * uph):.2f}/小时" if item.unit_price else "¥0.00/小时"
            
            quote_items.append({
                "id": item.id,
                "item_name": item.item_name,
                "item_description": item.item_description,
                "machine_type": item.machine_type,
                "supplier": item.supplier,
                "machine_model": item.machine_model,
                "configuration": item.configuration,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "machine_id": item.machine_id,
                "configuration_id": item.configuration_id,
                "uph": uph,
                "hourly_rate": hourly_rate
            })
        
        result = {
            "id": quote.id,
            "quote_number": quote.quote_number,
            "title": quote.title,
            "quote_type": quote.quote_type,
            "customer_name": quote.customer_name,
            "customer_contact": quote.customer_contact,
            "customer_phone": quote.customer_phone,
            "customer_email": quote.customer_email,
            "customer_address": quote.customer_address,
            "currency": quote.currency,
            "subtotal": quote.subtotal,
            "discount": quote.discount,
            "tax_rate": quote.tax_rate,
            "tax_amount": quote.tax_amount,
            "total_amount": quote.total_amount,
            "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
            "payment_terms": quote.payment_terms,
            "description": quote.description,
            "notes": quote.notes,
            "status": quote.status,
            "approval_status": quote.approval_status,  # 添加审批状态字段
            "version": quote.version,
            "submitted_at": quote.submitted_at.isoformat() if quote.submitted_at else None,
            "approved_at": quote.approved_at.isoformat() if quote.approved_at else None,
            "approved_by": quote.approved_by,
            "rejection_reason": quote.rejection_reason,
            "wecom_approval_id": quote.wecom_approval_id,
            "created_by": quote.created_by,
            "creator_name": creator_name,
            "created_at": quote.created_at.isoformat(),
            "updated_at": quote.updated_at.isoformat(),
            "items": quote_items
        }
        
        return result
        
    except Exception as e:
        print(f"获取报价单详情错误: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.get("/statistics", response_model=QuoteStatistics)
async def get_quote_statistics(
    db: Session = Depends(get_db)
):
    """获取报价单统计信息"""
    try:
        service = QuoteService(db)
        # 暂时不使用用户过滤，返回全部统计
        return service.get_quote_statistics(user_id=None)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/{quote_id}", response_model=QuoteSchema)
async def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID或报价单号获取报价单详情"""
    try:
        service = QuoteService(db)

        # 智能检测：如果是纯数字，按ID查询；否则按报价单号查询
        if quote_id.isdigit():
            quote = service.get_quote_by_id(int(quote_id))
        else:
            quote = service.get_quote_by_number(quote_id)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        if (quote.created_by != current_user.id and
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报价单"
            )

        return _quote_to_schema(service, quote)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(exc)}"
        )



@router.get("/number/{quote_number}", response_model=QuoteSchema)
async def get_quote_by_number(
    quote_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据报价单号获取报价单详情"""
    try:
        service = QuoteService(db)
        quote = service.get_quote_by_number(quote_number)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        if (quote.created_by != current_user.id and
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报价单"
            )

        return _quote_to_schema(service, quote)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(exc)}"
        )



@router.put("/{quote_id}", response_model=QuoteSchema)
async def update_quote(
    quote_id: str,
    quote_data: QuoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报价单"""
    logger = logging.getLogger("app.api.quotes")
    try:
        service = QuoteService(db)
        quote = service.update_quote(quote_id, quote_data, current_user.id)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        quote_detail = service.load_quote_with_details(quote.id) or quote
        _schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            True,
            "snapshot_generation_failed_on_update",
        )
        return _quote_to_schema(service, quote_detail)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        logger.exception("update_quote_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新报价单失败: {str(exc)}"
        )



@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报价单"""
    try:
        service = QuoteService(db)

        # 删除前先获取报价单信息（用于清理PDF缓存）
        quote = service.get_quote_by_id(quote_id)

        success = service.delete_quote(quote_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        if quote and quote.pdf_cache:
            try:
                pdf_path = Path(quote.pdf_cache.pdf_path)
                if not pdf_path.is_absolute():
                    pdf_path = Path(pdf_path)
                if pdf_path.exists():
                    pdf_path.unlink()
                parent_dir = pdf_path.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                logging.getLogger("app.snapshot").info(
                    json.dumps(
                        {
                            "event": "snapshot_cache_removed_on_delete",
                            "quote_id": quote.id,
                            "quote_number": quote.quote_number,
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception as cache_error:  # pragma: no cover - 删除缓存失败不阻断删除
                logging.getLogger("app.snapshot").warning(
                    json.dumps(
                        {
                            "event": "snapshot_cache_cleanup_failed",
                            "quote_id": quote.id if quote else quote_id,
                            "error": str(cache_error),
                        },
                        ensure_ascii=False,
                    )
                )

        return {"message": "报价单删除成功"}
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"删除报价单失败: {str(e)}"
        )


@router.post("/{quote_id}/restore")
async def restore_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复已删除的报价单"""
    try:
        service = QuoteService(db)
        success = service.restore_quote(quote_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在或未被删除"
            )

        return {"message": "报价单恢复成功"}
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"恢复报价单失败: {str(e)}"
        )


@router.patch("/{quote_id}/status", response_model=QuoteSchema)
async def update_quote_status(
    quote_id: str,
    status_update: QuoteStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报价单状态"""
    try:
        service = QuoteService(db)
        quote = service.update_quote_status(quote_id, status_update, current_user.id)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        return _quote_to_schema(service, quote)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新报价单状态失败: {str(exc)}"
        )



@router.post("/{quote_id}/submit", response_model=QuoteSchema)
async def submit_quote_for_approval(
    quote_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交报价单审批并确保PDF缓存可用"""
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
        _schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            False,
            "snapshot_generation_failed_on_submit",
        )
        return _quote_to_schema(service, quote_detail)
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



@router.get("/{quote_id}/approval-records", response_model=List[ApprovalRecord])
async def get_quote_approval_records(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报价单审批记录"""
    try:
        service = QuoteService(db)
        quote = service.get_quote_by_id(quote_id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # 检查访问权限
        if (quote.created_by != current_user.id and 
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报价单的审批记录"
            )
        
        records = service.get_approval_records(quote_id)
        return records
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
    """批准报价单"""
    try:
        service = QuoteService(db)

        if current_user.role not in ['admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行审批操作"
            )

        quote = service.approve_quote(quote_id, current_user.id, approval_data.get('comments', '审批通过'))
        quote_detail = service.load_quote_with_details(quote.id) or quote
        _schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            False,
            "snapshot_generation_failed_on_approve",
        )
        return {"message": "报价单已批准", "quote": _quote_to_schema(service, quote_detail)}
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
    """拒绝报价单"""
    try:
        service = QuoteService(db)

        if current_user.role not in ['admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行审批操作"
            )

        comments = rejection_data.get('comments', '')
        if not comments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="拒绝时必须提供拒绝原因"
            )

        quote = service.reject_quote(quote_id, current_user.id, comments)
        quote_detail = service.load_quote_with_details(quote.id) or quote
        _schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            False,
            "snapshot_generation_failed_on_reject",
        )
        return {"message": "报价单已拒绝", "quote": _quote_to_schema(service, quote_detail)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"拒绝操作失败: {str(exc)}"
        )



@router.get("/{quote_id}/export/pdf")
async def export_quote_pdf(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出报价单PDF - 占位实现"""
    try:
        service = QuoteService(db)
        quote = service.get_quote_by_id(quote_id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # 检查访问权限
        if (quote.created_by != current_user.id and 
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限导出此报价单"
            )
        
        # TODO: 实现PDF生成逻辑
        from ....services.outbox import outbox
        outbox.add("generate_export", {"quote_id": quote_id, "format": "pdf"})
        
        return {
            "message": "PDF导出任务已创建",
            "quote_id": quote_id,
            "format": "pdf",
            "status": "processing"
        }
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
    current_user: User = Depends(get_current_user)
):
    """导出报价单Excel - 占位实现"""
    try:
        service = QuoteService(db)
        quote = service.get_quote_by_id(quote_id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # 检查访问权限
        if (quote.created_by != current_user.id and 
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限导出此报价单"
            )
        
        # TODO: 实现Excel生成逻辑
        from ....services.outbox import outbox
        outbox.add("generate_export", {"quote_id": quote_id, "format": "excel"})
        
        return {
            "message": "Excel导出任务已创建",
            "quote_id": quote_id,
            "format": "excel", 
            "status": "processing"
        }
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
    current_user: User = Depends(get_current_user)
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

        base_query = db.query(QuoteModel).options(
            selectinload(QuoteModel.items),
            selectinload(QuoteModel.creator),
            selectinload(QuoteModel.pdf_cache),
        )

        quote = None
        # 简单判断是否为数字ID或UUID
        if quote_id.isdigit():
            quote = base_query.filter(QuoteModel.id == int(quote_id), QuoteModel.is_deleted == False).first()
        else:
            from uuid import UUID
            try:
                UUID(quote_id)
                quote = base_query.filter(QuoteModel.uuid == quote_id, QuoteModel.is_deleted == False).first()
            except (ValueError, AttributeError):
                quote = base_query.filter(QuoteModel.quote_number == quote_id, QuoteModel.is_deleted == False).first()

        if not quote:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报价单不存在")

        if (quote.created_by != current_user.id and current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此报价单")

        service = QuoteService(db)
        try:
            cache = await asyncio.to_thread(
                service.ensure_pdf_cache, quote, current_user, False, column_configs, True, False
            )
        except PDFGenerationInProgress:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PDF生成中，请稍后再试")
        pdf_path = Path(cache.pdf_path)
        if not pdf_path.is_absolute():
            pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PDF生成中，请稍后再试")

        filename = f"{quote.quote_number}_quote.pdf"
        disposition = "attachment" if download else "inline"
        from urllib.parse import quote as url_quote
        encoded = url_quote(f"{quote.quote_number}_报价单.pdf")
        headers = {
            "Content-Disposition": f"{disposition}; filename=\"{filename}\"; filename*=UTF-8''{encoded}",
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
