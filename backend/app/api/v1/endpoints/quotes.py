"""
报价单相关的API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import json

from ....database import get_db
from ....services.quote_service import QuoteService
from ....services.weasyprint_pdf_service import WeasyPrintPDFService
from ....schemas import (
    Quote, QuoteCreate, QuoteUpdate, QuoteList, 
    QuoteFilter, QuoteStatusUpdate, QuoteStatistics,
    ApprovalRecord
)
from ....auth import get_current_user
from ....models import User

router = APIRouter(prefix="/quotes", tags=["报价单管理"])


@router.post("/", response_model=Quote, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新报价单"""
    try:
        # 🚨 紧急调试：记录完整的创建请求数据
        print(f"🚨 CREATE_QUOTE_DEBUG:")
        print(f"   用户ID: {current_user.id}")
        print(f"   报价类型: {quote_data.quote_type}")
        print(f"   项目数量: {len(quote_data.items) if quote_data.items else 0}")
        
        if quote_data.items:
            print(f"   项目明细:")
            for i, item in enumerate(quote_data.items, 1):
                print(f"     {i}. {item.item_name} | 描述:{getattr(item, 'item_description', 'N/A')} | 数量:{item.quantity}")
        
        service = QuoteService(db)
        quote = service.create_quote(quote_data, current_user.id)
        
        # 调试：打印返回的quote对象
        print(f"✅ 报价单创建完成: ID={quote.id}, 报价单号={quote.quote_number}")

        # 异步生成PDF - 在后台开始生成，不阻塞响应
        import threading

        def generate_pdf_background():
            try:
                print(f"📝 开始后台生成PDF for 报价单 {quote.id}")
                from ....services.weasyprint_pdf_service import weasyprint_pdf_service
                from ....models import Quote
                import os
                import hashlib

                # 重新获取完整报价数据
                bg_db = next(get_db())
                try:
                    from sqlalchemy.orm import selectinload
                    bg_quote = (bg_db.query(Quote)
                              .options(selectinload(Quote.items), selectinload(Quote.creator))
                              .filter(Quote.id == quote.id)
                              .first())

                    if bg_quote:
                        # 准备PDF数据
                        type_mapping = {
                            'inquiry': '询价报价',
                            'tooling': '工装夹具报价',
                            'engineering': '工程机时报价',
                            'mass_production': '量产机时报价',
                            'process': '量产工序报价',
                            'comprehensive': '综合报价'
                        }

                        quote_dict = {
                            'quote_number': bg_quote.quote_number,
                            'customer': bg_quote.customer_name,
                            'type': type_mapping.get(bg_quote.quote_type, bg_quote.quote_type),
                            'currency': bg_quote.currency or 'RMB',
                            'createdBy': bg_quote.creator.name if bg_quote.creator else '未知',
                            'createdAt': bg_quote.created_at.strftime('%Y-%m-%d %H:%M:%S') if bg_quote.created_at else '',
                            'updatedAt': bg_quote.updated_at.strftime('%Y-%m-%d %H:%M:%S') if bg_quote.updated_at else '',
                            'validUntil': bg_quote.valid_until.strftime('%Y-%m-%d') if bg_quote.valid_until else '',
                            'items': [
                                {
                                    'machineType': item.machine_type,
                                    'machineModel': item.machine_model,
                                    'itemName': getattr(item, 'item_name', ''),
                                    'itemDescription': item.item_description,
                                    'quantity': float(item.quantity),
                                    'unit': getattr(item, 'unit', ''),
                                    'unitPrice': float(item.unit_price),
                                    'totalPrice': float(item.total_price)
                                }
                                for item in bg_quote.items
                            ]
                        }

                        # 生成PDF并缓存
                        cache_dir = "pdf_cache"
                        os.makedirs(cache_dir, exist_ok=True)
                        cache_key = hashlib.md5(f"{bg_quote.id}_{bg_quote.updated_at}".encode()).hexdigest()
                        cache_file = os.path.join(cache_dir, f"{cache_key}.pdf")

                        pdf_data = weasyprint_pdf_service.generate_quote_pdf(quote_dict)
                        with open(cache_file, 'wb') as f:
                            f.write(pdf_data)

                        print(f"✅ 报价单 {quote.id} PDF后台生成完成，缓存到: {cache_file}")
                    else:
                        print(f"⚠️ 无法获取报价单 {quote.id} 数据，跳过PDF生成")
                finally:
                    bg_db.close()

            except Exception as e:
                print(f"⚠️ 报价单 {quote.id} PDF后台生成失败: {str(e)}")

        # 启动后台线程生成PDF
        pdf_thread = threading.Thread(target=generate_pdf_background)
        pdf_thread.daemon = True  # 设为守护线程，主程序退出时自动结束
        pdf_thread.start()

        print(f"📝 报价单 {quote.id} 创建成功，PDF正在后台生成")

        return quote
    except Exception as e:
        print(f"🚨 创建报价单异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建报价单失败: {str(e)}"
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
    """获取报价单列表"""
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
        
        return {
            "items": quotes,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    except Exception as e:
        print(f"API错误详情: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报价单列表失败: {str(e)}"
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


@router.get("/{quote_id}", response_model=Quote)
async def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID获取报价单详情"""
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
                detail="无权限访问此报价单"
            )
        
        return quote
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(e)}"
        )


@router.get("/number/{quote_number}", response_model=Quote)
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
        
        # 检查访问权限
        if (quote.created_by != current_user.id and 
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报价单"
            )
        
        return quote
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(e)}"
        )


@router.put("/{quote_id}", response_model=Quote)
async def update_quote(
    quote_id: str,
    quote_data: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报价单"""
    try:
        service = QuoteService(db)
        quote = service.update_quote(quote_id, quote_data, current_user.id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        return quote
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
            detail=f"更新报价单失败: {str(e)}"
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

        # 清理对应的PDF缓存文件
        if quote:
            try:
                import os
                import hashlib
                import glob

                cache_dir = "pdf_cache"
                # 删除所有与此报价单ID相关的缓存文件（因为可能有多个版本）
                pattern = f"{cache_dir}/*{quote.id}*"
                cache_files = glob.glob(pattern)

                # 也按哈希查找
                cache_key = hashlib.md5(f"{quote.id}_{quote.updated_at}".encode()).hexdigest()
                cache_file = os.path.join(cache_dir, f"{cache_key}.pdf")
                if os.path.exists(cache_file):
                    cache_files.append(cache_file)

                for cache_file in cache_files:
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                        print(f"🗑️ 已删除PDF缓存文件: {cache_file}")

                if cache_files:
                    print(f"✅ 报价单 {quote_id} 删除完成，已清理 {len(cache_files)} 个PDF缓存文件")
                else:
                    print(f"📝 报价单 {quote_id} 删除完成，未找到PDF缓存文件")

            except Exception as cache_error:
                print(f"⚠️ 清理PDF缓存时出错（不影响删除操作）: {str(cache_error)}")

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


@router.patch("/{quote_id}/status", response_model=Quote)
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
        
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新报价单状态失败: {str(e)}"
        )


@router.post("/{quote_id}/submit", response_model=Quote)
async def submit_quote_for_approval(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交报价单审批"""
    try:
        service = QuoteService(db)
        quote = service.submit_for_approval(quote_id, current_user.id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # TODO: 这里将来集成企业微信审批API
        # wecom_service = WeComApprovalService()
        # approval_id = wecom_service.submit_approval(quote)
        # quote.wecom_approval_id = approval_id
        
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提交审批失败: {str(e)}"
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批准报价单"""
    try:
        service = QuoteService(db)
        
        # 检查权限 - 只有管理员可以审批
        if current_user.role not in ['admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行审批操作"
            )
        
        quote = service.approve_quote(quote_id, current_user.id, approval_data.get('comments', '审批通过'))
        return {"message": "报价单已批准", "quote": quote}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批准操作失败: {str(e)}"
        )


@router.post("/{quote_id}/reject")
async def reject_quote(
    quote_id: str,
    rejection_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝报价单"""
    try:
        service = QuoteService(db)
        
        # 检查权限 - 只有管理员可以审批
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
        return {"message": "报价单已拒绝", "quote": quote}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"拒绝操作失败: {str(e)}"
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
    """
    获取报价单PDF - 支持预览和下载

    Args:
        quote_id: 报价单ID
        download: 是否作为下载文件返回
        db: 数据库会话
        current_user: 当前用户

    Returns:
        PDF文件流
    """
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy.orm import selectinload
        import uuid

        # 检测quote_id类型并选择合适的查询方式
        quote = None

        # 检查是否为UUID格式
        try:
            uuid.UUID(quote_id)
            # UUID格式，使用uuid字段查询
            quote = (db.query(Quote)
                    .options(selectinload(Quote.items), selectinload(Quote.creator))
                    .filter(Quote.uuid == quote_id, Quote.is_deleted == False)
                    .first())
        except ValueError:
            # 检查是否为纯数字（ID）
            if quote_id.isdigit():
                # 数字ID
                quote = (db.query(Quote)
                        .options(selectinload(Quote.items), selectinload(Quote.creator))
                        .filter(Quote.id == int(quote_id), Quote.is_deleted == False)
                        .first())
            else:
                # 报价单号
                quote = (db.query(Quote)
                        .options(selectinload(Quote.items), selectinload(Quote.creator))
                        .filter(Quote.quote_number == quote_id, Quote.is_deleted == False)
                        .first())

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
                detail="无权限访问此报价单"
            )

        # 导入PDF生成服务
        from ....services.weasyprint_pdf_service import weasyprint_pdf_service

        # 类型映射：英文 -> 中文
        type_mapping = {
            'inquiry': '询价报价',
            'tooling': '工装夹具报价',
            'engineering': '工程机时报价',
            'mass_production': '量产机时报价',
            'process': '量产工序报价',
            'comprehensive': '综合报价'
        }

        # 解析前端传递的列配置
        column_configs = None
        if columns:
            try:
                column_configs = json.loads(columns)
                print(f"📊 收到前端列配置: {column_configs}")
            except json.JSONDecodeError:
                print(f"⚠️ 列配置JSON解析失败，使用默认配置")

        # 准备报价单数据
        quote_dict = {
            'quote_number': quote.quote_number,
            'customer': quote.customer_name,
            'type': type_mapping.get(quote.quote_type, quote.quote_type),  # 转换为中文类型
            'currency': quote.currency or 'RMB',
            'createdBy': current_user.name,
            'createdAt': quote.created_at.strftime('%Y-%m-%d %H:%M:%S') if quote.created_at else '',
            'updatedAt': quote.updated_at.strftime('%Y-%m-%d %H:%M:%S') if quote.updated_at else '',
            'validUntil': quote.valid_until.strftime('%Y-%m-%d') if quote.valid_until else '',
            'items': [
                {
                    'machineType': item.machine_type,
                    'machineModel': item.machine_model,
                    'itemName': getattr(item, 'item_name', ''),
                    'itemDescription': item.item_description,
                    'quantity': float(item.quantity),
                    'unit': getattr(item, 'unit', ''),
                    'unitPrice': float(item.unit_price),
                    'totalPrice': float(item.total_price)
                }
                for item in quote.items
            ],
            'columnConfigs': column_configs  # 传递列配置给PDF服务
        }

        # PDF缓存机制
        import os
        import hashlib
        cache_dir = "pdf_cache"
        os.makedirs(cache_dir, exist_ok=True)

        # 基于报价单数据生成缓存key
        cache_key = hashlib.md5(f"{quote.id}_{quote.updated_at}".encode()).hexdigest()
        cache_file = os.path.join(cache_dir, f"{cache_key}.pdf")

        # 检查缓存文件是否存在
        if os.path.exists(cache_file):
            print(f"📄 使用缓存PDF: {cache_file}")
            with open(cache_file, 'rb') as f:
                pdf_data = f.read()
        else:
            print(f"📝 生成新PDF并缓存: {cache_file}")
            # 生成PDF
            pdf_data = weasyprint_pdf_service.generate_quote_pdf(quote_dict)
            # 保存到缓存
            with open(cache_file, 'wb') as f:
                f.write(pdf_data)

        # 生成文件名 - 避免中文编码问题
        from urllib.parse import quote as url_quote
        filename = f"{quote.quote_number}_quote.pdf"
        filename_encoded = url_quote(f"{quote.quote_number}_报价单.pdf")

        # 设置响应头
        headers = {
            "Content-Type": "application/pdf",
            "Content-Length": str(len(pdf_data))
        }

        if download:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename_encoded}'
        else:
            headers["Content-Disposition"] = f'inline; filename="{filename}"; filename*=UTF-8\'\'{filename_encoded}'

        from fastapi.responses import Response
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers=headers
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF生成失败: {str(e)}"
        )