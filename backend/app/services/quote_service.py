"""
报价单服务层
处理报价单相关的业务逻辑
"""

import logging
from threading import Thread
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.exc import IntegrityError

from ..models import Quote, QuoteItem, ApprovalRecord, User, QuotePDFCache
from ..schemas import (
    QuoteCreate, QuoteUpdate, QuoteFilter,
    QuoteStatusUpdate, ApprovalRecordCreate,
    QuoteStatistics
)
from .frontend_snapshot_pdf_service import (
    get_frontend_snapshot_pdf_service,
    upsert_pdf_cache,
)

logger = logging.getLogger(__name__)


class PDFGenerationInProgress(Exception):
    """Raised when a PDF generation task is already in progress."""


class QuoteService:
    """报价单服务类"""

    MONEY_QUANTIZE = Decimal("0.01")
    RATE_QUANTIZE = Decimal("0.0001")
    STATUS_TO_APPROVAL = {
        "draft": "not_submitted",
        "pending": "pending",
        "approved": "approved",
        "rejected": "rejected",
        "returned": "returned_for_revision",
        "forwarded": "forwarded",
    }
    APPROVAL_TO_STATUS = {
        "not_submitted": "draft",
        "pending": "pending",
        "approved": "approved",
        "rejected": "rejected",
        "returned_for_revision": "returned",
        "forwarded": "forwarded",
    }

    def __init__(self, db: Session):
        self.db = db

    # --------- 工具方法 ---------

    def _to_decimal(self, value, field_name: str) -> Decimal:
        """将输入转换为Decimal，非法值抛出友好错误"""
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            raise ValueError(f"字段 {field_name} 的值无效: {value}")

    def _quantize_money(self, value: Decimal) -> Decimal:
        return value.quantize(self.MONEY_QUANTIZE, rounding=ROUND_HALF_UP)

    def _normalize_discount(self, subtotal: Decimal, discount_value, field_name: str = "discount") -> Decimal:
        discount = self._to_decimal(discount_value, field_name)
        if discount < 0:
            raise ValueError("折扣金额不能为负数")
        if discount > subtotal:
            discount = subtotal
        return self._quantize_money(discount)

    def _normalize_tax_rate(self, tax_rate_value, field_name: str = "tax_rate") -> Decimal:
        tax_rate = self._to_decimal(tax_rate_value if tax_rate_value is not None else 0, field_name)
        if tax_rate < 0 or tax_rate > 1:
            raise ValueError("税率必须在0到1之间")
        return tax_rate.quantize(self.RATE_QUANTIZE, rounding=ROUND_HALF_UP)

    def _prepare_items(self, quote: Quote, discount=None, tax_rate=None):
        """根据现有 QuoteItem 重新计算金额字段"""
        items = quote.items
        subtotal = Decimal("0")
        for index, item in enumerate(items, start=1):
            quantity = self._to_decimal(item.quantity, f"items[{index}].quantity")
            if quantity < 0:
                raise ValueError("数量不能为负数")
            unit_price = self._to_decimal(item.unit_price, f"items[{index}].unit_price")
            if unit_price < 0:
                raise ValueError("单价不能为负数")
            total_price = self._quantize_money(quantity * unit_price)
            item.total_price = float(total_price)
            subtotal += total_price

        discount_source = discount if discount is not None else quote.discount
        tax_rate_source = tax_rate if tax_rate is not None else quote.tax_rate
        discount_decimal = self._normalize_discount(subtotal, discount_source)
        tax_rate_decimal = self._normalize_tax_rate(tax_rate_source)
        taxable_base = self._quantize_money(subtotal - discount_decimal)
        tax_amount = self._quantize_money(taxable_base * tax_rate_decimal)
        total_amount = taxable_base + tax_amount

        return {
            "subtotal": float(self._quantize_money(subtotal)),
            "discount": float(discount_decimal),
            "tax_rate": float(tax_rate_decimal),
            "tax_amount": float(tax_amount),
            "total_amount": float(self._quantize_money(total_amount)),
        }

    def _prepare_items_payload(self, item_models: List[Any]) -> Dict[str, Any]:
        prepared_items = []
        subtotal = Decimal("0")
        for index, item_data in enumerate(item_models, start=1):
            if hasattr(item_data, "model_dump"):
                item_dict = item_data.model_dump(exclude_unset=True)
            else:
                item_dict = dict(item_data)
            quantity = self._to_decimal(item_dict.get("quantity", 0), f"items[{index}].quantity")
            if quantity < 0:
                raise ValueError("数量不能为负数")
            unit_price = self._to_decimal(item_dict.get("unit_price", 0), f"items[{index}].unit_price")
            if unit_price < 0:
                raise ValueError("单价不能为负数")

            total_price = self._quantize_money(quantity * unit_price)

            item_dict["quantity"] = float(quantity)
            item_dict["unit_price"] = float(unit_price)
            item_dict["total_price"] = float(total_price)

            prepared_items.append(item_dict)
            subtotal += total_price

        return {"items": prepared_items, "subtotal": subtotal}

    def _apply_financials_to_quote(self, quote: Quote, discount_override=None, tax_rate_override=None):
        """重新计算并回写报价单金额字段"""
        totals = self._prepare_items(quote, discount_override, tax_rate_override)
        quote.subtotal = totals["subtotal"]
        quote.discount = totals["discount"]
        quote.tax_rate = totals["tax_rate"]
        quote.tax_amount = totals["tax_amount"]
        quote.total_amount = totals["total_amount"]

    def _status_payload(self, status: str = None, approval_status: Optional[str] = None) -> Dict[str, str]:
        status = status or "draft"
        derived_approval = approval_status or self.STATUS_TO_APPROVAL.get(status, "not_submitted")
        derived_status = self.APPROVAL_TO_STATUS.get(derived_approval, status)
        return {"status": derived_status, "approval_status": derived_approval}

    def _sync_status_fields(self, quote: Quote, status: Optional[str] = None, approval_status: Optional[str] = None):
        payload = self._status_payload(status, approval_status)
        quote.status = payload["status"]
        quote.approval_status = payload["approval_status"]

    def load_quote_with_details(self, quote_id: int) -> Optional[Quote]:
        return (
            self.db.query(Quote)
            .options(
                selectinload(Quote.items),
                selectinload(Quote.creator),
                selectinload(Quote.pdf_cache),
            )
            .filter(Quote.id == quote_id, Quote.is_deleted == False)
            .first()
        )

    def ensure_pdf_cache(
        self,
        quote: Quote,
        user,
        force: bool = False,
        column_configs: Optional[Dict] = None,
        prefer_playwright: bool = False,
        wait: bool = True,
    ):
        service = get_frontend_snapshot_pdf_service()
        current_hash = service.compute_quote_hash(quote, column_configs)
        cache = quote.pdf_cache
        needs_regen = force or cache is None
        cached_path = service.get_cached_pdf_path(quote) if cache is not None else None
        file_ready = cached_path is not None
        async_regen = False

        if not needs_regen and cache is not None:
            if cache.status == 'generating' and not force:
                if file_ready and cache.content_hash == current_hash:
                    cache.status = 'ready'
                    cache.last_error = None
                    self.db.flush()
                else:
                    raise PDFGenerationInProgress()
            if cache.status == 'error':
                needs_regen = True
            elif not file_ready:
                needs_regen = True
            elif cache.content_hash and cache.content_hash != current_hash:
                needs_regen = True
            elif cache.content_hash is None:
                cache.content_hash = current_hash
                cache.updated_at = quote.updated_at or cache.updated_at
                self.db.flush()
            elif prefer_playwright and cache.source != 'playwright':
                if wait:
                    needs_regen = True
                else:
                    async_regen = True
            elif quote.updated_at and cache.updated_at and quote.updated_at > cache.updated_at:
                cache.updated_at = quote.updated_at
                self.db.flush()
            elif cache.source not in ('playwright', 'weasyprint'):
                needs_regen = True

        if needs_regen:
            if not wait:
                cache = self._mark_pdf_generating(quote, cache, current_hash)
                self._schedule_pdf_generation(quote.id, getattr(user, 'id', None), column_configs, prefer_playwright)
                raise PDFGenerationInProgress()

            cache = self._mark_pdf_generating(quote, cache, current_hash)
            try:
                result = service.generate_with_fallback(quote, user, self.db, column_configs=column_configs)
                result.setdefault('content_hash', current_hash)
                result.setdefault('status', 'ready')
                cache = upsert_pdf_cache(self.db, quote, result)
            except Exception as exc:
                self._mark_pdf_failed(cache, str(exc))
                raise
        elif async_regen and cache.status != 'generating':
            self._schedule_pdf_generation(quote.id, getattr(user, 'id', None), column_configs, True)
        return cache

    def _mark_pdf_generating(
        self,
        quote: Quote,
        cache: Optional[QuotePDFCache],
        content_hash: str,
    ) -> QuotePDFCache:
        now = datetime.utcnow()
        if cache is None:
            cache = QuotePDFCache(
                quote_id=quote.id,
                pdf_path=f"media/quotes/{quote.id}/quote_{quote.quote_number}.pdf",
                source='pending',
                file_size=0,
                status='generating',
                content_hash=content_hash,
                updated_at=now,
            )
            self.db.add(cache)
            quote.pdf_cache = cache
        else:
            cache.status = 'generating'
            cache.last_error = None
            cache.content_hash = content_hash
            cache.updated_at = now
        self.db.commit()
        return cache

    def _mark_pdf_failed(self, cache: QuotePDFCache, error_message: str):
        cache.status = 'error'
        cache.last_error = error_message[:500]
        cache.updated_at = datetime.utcnow()
        self.db.commit()

    def _schedule_pdf_generation(
        self,
        quote_id: int,
        user_id: Optional[int],
        column_configs: Optional[Dict],
        prefer_playwright: bool,
    ):
        from ..database import SessionLocal

        def task():
            with SessionLocal() as session:
                service = QuoteService(session)
                quote = (
                    session.query(Quote)
                    .options(selectinload(Quote.items), selectinload(Quote.pdf_cache))
                    .filter(Quote.id == quote_id)
                    .first()
                )
                if not quote:
                    logger.warning("quote_not_found_for_pdf", extra={"quote_id": quote_id})
                    return

                user = None
                if user_id:
                    user = session.query(User).filter(User.id == user_id).first()
                if user is None and quote.created_by:
                    user = session.query(User).filter(User.id == quote.created_by).first()
                if user is None:
                    user = (
                        session.query(User)
                        .filter(User.role.in_(['admin', 'super_admin']))
                        .order_by(User.id.asc())
                        .first()
                    )

                if user is None:
                    logger.error("pdf_generation_no_user", extra={"quote_id": quote_id})
                    if quote.pdf_cache:
                        service._mark_pdf_failed(quote.pdf_cache, "缺少可用的用户用于生成PDF")
                    return

                try:
                    service.ensure_pdf_cache(
                        quote,
                        user,
                        force=True,
                        column_configs=column_configs,
                        prefer_playwright=prefer_playwright,
                        wait=True,
                    )
                except Exception as exc:
                    logger.error("pdf_generation_async_failed", extra={"quote_id": quote_id, "error": str(exc)})

        Thread(target=task, daemon=True).start()

    def get_pdf_url(self, quote: Quote) -> Optional[str]:
        if getattr(quote, 'pdf_cache', None):
            service = get_frontend_snapshot_pdf_service()
            return service.build_public_url_from_cache(quote.pdf_cache)
        return getattr(quote, "pdf_url", None)

    def get_quote_unit_abbreviation(self, quote_unit: str) -> str:
        """获取报价单位缩写"""
        unit_mapping = {
            "昆山芯信安": "KS",
            "苏州芯昱安": "SZ", 
            "上海芯睿安": "SH",
            "珠海芯创安": "ZH"
        }
        return unit_mapping.get(quote_unit, "KS")  # 默认返回KS

    def generate_quote_number(self, quote_unit: str = "昆山芯信安") -> str:
        """生成报价单号: CIS-{单位缩写}{年月日}{顺序编号}"""
        # 获取单位缩写
        unit_abbr = self.get_quote_unit_abbreviation(quote_unit)

        # 获取当前日期
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")

        # 查找当日该单位的最大编号（包括所有记录以避免编号冲突）
        prefix = f"CIS-{unit_abbr}{date_str}"
        latest_quote = (
            self.db.query(Quote)
            .filter(Quote.quote_number.like(f"{prefix}%"))
            # 不过滤软删除记录，避免编号冲突
            .order_by(desc(Quote.quote_number))
            .first()
        )

        if latest_quote:
            # 提取序号并加1
            try:
                seq = int(latest_quote.quote_number[-3:]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"

    def create_quote(self, quote_data: QuoteCreate, user_id: int) -> Quote:
        """创建报价单"""
        # 根据报价类型决定初始状态
        # 询价报价直接设为已批准状态，其他类型设为草稿需要审批
        if quote_data.quote_type == 'inquiry':
            initial_status = 'approved'
            approved_by = user_id
            approved_at = datetime.now()
        else:
            initial_status = 'draft'
            approved_by = None
            approved_at = None
        
        # 创建报价单主记录
        base_data = quote_data.model_dump(exclude={'items'})

        prepared = self._prepare_items_payload(quote_data.items)
        discount_decimal = self._normalize_discount(prepared["subtotal"], base_data.get('discount'))
        tax_rate_decimal = self._normalize_tax_rate(base_data.get('tax_rate'))
        taxable_base = self._quantize_money(prepared["subtotal"] - discount_decimal)
        tax_amount = self._quantize_money(taxable_base * tax_rate_decimal)
        total_amount = self._quantize_money(taxable_base + tax_amount)

        financial_payload = {
            'created_by': user_id,
            'approved_by': approved_by,
            'approved_at': approved_at,
            'subtotal': float(self._quantize_money(prepared["subtotal"])),
            'discount': float(discount_decimal),
            'tax_rate': float(tax_rate_decimal),
            'tax_amount': float(tax_amount),
            'total_amount': float(total_amount),
            'approval_method': 'internal',
        }
        financial_payload.update(self._status_payload(initial_status))

        max_attempts = 5
        last_exception = None

        for attempt in range(max_attempts):
            current_quote_number = self.generate_quote_number(quote_data.quote_unit)
            quote_payload = {
                **base_data,
                **financial_payload,
                'quote_number': current_quote_number,
            }

            quote = Quote(**quote_payload)
            self.db.add(quote)
            self.db.flush()

            # 创建报价明细
            for item_template in prepared["items"]:
                item_dict = {**item_template, 'quote_id': quote.id}
                self.db.add(QuoteItem(**item_dict))

            # 如果是询价报价，创建审批记录表示自动批准
            if quote_data.quote_type == 'inquiry':
                approval_record = ApprovalRecord(
                    quote_id=quote.id,
                    action='auto_approve_inquiry',
                    status='approved',
                    approver_id=user_id,
                    comments='询价报价自动批准，无需审批流程',
                    processed_at=datetime.now()
                )
                self.db.add(approval_record)

            try:
                self.db.commit()
                self.db.refresh(quote)
                from sqlalchemy.orm import selectinload
                created_quote = (
                    self.db.query(Quote)
                    .options(selectinload(Quote.items))
                    .filter(Quote.id == quote.id)
                    .first()
                )
                return created_quote
            except IntegrityError as exc:
                self.db.rollback()
                last_exception = exc
                if 'quote_number' in str(exc).lower() and attempt < max_attempts - 1:
                    continue
                raise

        raise last_exception or ValueError("生成报价单号失败")

    def get_quote_by_id(self, quote_id: int) -> Optional[Quote]:
        """根据ID获取报价单"""
        return (
            self.db.query(Quote)
            .options(selectinload(Quote.pdf_cache))
            .filter(Quote.id == quote_id, Quote.is_deleted == False)
            .first()
        )

    def get_quote_by_number(self, quote_number: str) -> Optional[Quote]:
        """根据报价单号获取报价单"""
        return (
            self.db.query(Quote)
            .options(
                selectinload(Quote.items),
                selectinload(Quote.creator),
                selectinload(Quote.pdf_cache),
            )
            .filter(Quote.quote_number == quote_number, Quote.is_deleted == False)
            .first()
        )

    def get_quotes(self, filter_params: QuoteFilter, user_id: Optional[int] = None):
        """获取报价单列表"""
        # 构建基础查询
        base_filters = [Quote.is_deleted == False]  # 默认过滤软删除数据

        # 应用筛选条件
        if filter_params.status:
            base_filters.append(Quote.status == filter_params.status)

        if filter_params.quote_type:
            base_filters.append(Quote.quote_type == filter_params.quote_type)

        if filter_params.customer_name:
            base_filters.append(Quote.customer_name.contains(filter_params.customer_name))

        if filter_params.created_by:
            base_filters.append(Quote.created_by == filter_params.created_by)
        elif user_id:
            # 权限过滤：用户只能看到自己和比自己权限更低的用户创建的报价单
            # 权限等级定义（从高到低）
            role_hierarchy = {
                'super_admin': 4,
                'admin': 3,
                'manager': 2,
                'user': 1
            }

            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                current_role_level = role_hierarchy.get(user.role, 0)

                # 查询所有权限等级严格小于当前用户的用户ID
                allowed_user_ids = [user_id]  # 包括自己
                all_users = self.db.query(User).filter(User.is_active == True).all()
                for u in all_users:
                    u_role_level = role_hierarchy.get(u.role, 0)
                    if u_role_level < current_role_level and u.id != user_id:  # 改为严格小于，同级用户不能互相看到
                        allowed_user_ids.append(u.id)

                # 过滤报价单：只显示允许的用户创建的报价单
                base_filters.append(Quote.created_by.in_(allowed_user_ids))
        
        if filter_params.date_from:
            base_filters.append(Quote.created_at >= filter_params.date_from)
        
        if filter_params.date_to:
            base_filters.append(Quote.created_at <= filter_params.date_to)
        
        # 计算总数
        count_query = self.db.query(Quote)
        if base_filters:
            count_query = count_query.filter(and_(*base_filters))
        total = count_query.count()

        # 获取分页数据
        data_query = self.db.query(Quote).options(
            selectinload(Quote.pdf_cache)
        )
        if base_filters:
            data_query = data_query.filter(and_(*base_filters))
            
        quotes = (
            data_query.order_by(desc(Quote.created_at))
            .offset((filter_params.page - 1) * filter_params.size)
            .limit(filter_params.size)
            .all()
        )
        
        return quotes, total

    def update_quote(self, quote_id: int, quote_data: QuoteUpdate, user_id: int) -> Optional[Quote]:
        """更新报价单"""
        quote = self.get_quote_by_id(quote_id)
        if not quote:
            return None
        
        # 检查权限：只有创建者或管理员可以编辑
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or (quote.created_by != user_id and user.role not in ['admin', 'super_admin']):
            raise PermissionError("无权限编辑此报价单")
        
        # 检查状态：只有草稿和被驳回状态可以编辑
        if quote.status not in ['draft', 'rejected']:
            raise ValueError("只有草稿或被驳回状态的报价单可以编辑")
        
        # 更新报价单字段
        payload = quote_data.model_dump(exclude_unset=True)
        items_payload = payload.pop('items', None)

        discount_override = payload.pop('discount', None) if 'discount' in payload else None
        tax_rate_override = payload.pop('tax_rate', None) if 'tax_rate' in payload else None

        # 忽略客户端传来的金额字段，统一由后台计算
        payload.pop('subtotal', None)
        payload.pop('tax_amount', None)
        payload.pop('total_amount', None)

        for field, value in payload.items():
            setattr(quote, field, value)

        # 更新报价明细
        if items_payload is not None:
            # 删除旧的明细项
            self.db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).delete()

            # 添加新的明细项
            prepared = self._prepare_items_payload(items_payload)
            for item_dict in prepared["items"]:
                item_dict['quote_id'] = quote_id
                item = QuoteItem(**item_dict)
                self.db.add(item)
            self.db.flush()
        
        # 重新加载明细（确保关系可用）
        self.db.refresh(quote)
        self._apply_financials_to_quote(quote, discount_override, tax_rate_override)

        quote.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(quote)
        return quote

    def delete_quote(self, quote_id: int, user_id: int) -> bool:
        """删除报价单"""
        quote = self.get_quote_by_id(quote_id)
        if not quote:
            return False
        
        # 检查权限
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise PermissionError("用户不存在")
        
        # 权限检查：管理员可以删除任何报价单，普通用户只能删除自己创建的
        is_admin = user.role in ['admin', 'super_admin']
        is_owner = quote.created_by == user_id
        
        if not is_admin and not is_owner:
            raise PermissionError("无权限删除此报价单")
        
        # 状态检查：普通用户只能删除草稿状态，管理员可以删除任何状态
        if not is_admin and quote.status != 'draft':
            raise ValueError("普通用户只能删除草稿状态的报价单")
        
        # 软删除：设置删除标记而不是实际删除
        quote.is_deleted = True
        quote.deleted_at = datetime.utcnow()
        quote.deleted_by = user_id

        self.db.commit()
        return True

    def restore_quote(self, quote_id: int, user_id: int) -> bool:
        """恢复删除的报价单"""
        # 查询包括软删除的报价单
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote or not quote.is_deleted:
            return False

        # 检查权限：只有管理员可以恢复
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.role not in ['admin', 'super_admin']:
            raise PermissionError("只有管理员可以恢复已删除的报价单")

        # 恢复报价单
        quote.is_deleted = False
        quote.deleted_at = None
        quote.deleted_by = None

        self.db.commit()
        return True

    def update_quote_status(self, quote_id: int, status_update: QuoteStatusUpdate, user_id: int) -> Optional[Quote]:
        """更新报价单状态"""
        quote = self.get_quote_by_id(quote_id)
        if not quote:
            return None
        
        # 验证状态转换
        valid_statuses = ['draft', 'pending', 'approved', 'rejected']
        if status_update.status not in valid_statuses:
            raise ValueError(f"无效的状态: {status_update.status}")
        
        # 状态转换规则
        status_transitions = {
            'draft': ['pending'],
            'pending': ['approved', 'rejected', 'draft'],
            'approved': [],  # 已批准的不能再改变状态
            'rejected': ['draft']  # 被拒绝的可以重新修改为草稿
        }
        
        if status_update.status not in status_transitions.get(quote.status, []):
            raise ValueError(f"不能从 {quote.status} 状态转换到 {status_update.status} 状态")
        
        # 更新状态
        old_status = quote.status
        self._sync_status_fields(quote, status=status_update.status)

        # 根据状态更新相应字段
        if status_update.status == 'pending':
            quote.submitted_at = datetime.now()
            quote.approval_method = quote.approval_method or 'internal'
        elif status_update.status == 'approved':
            quote.approved_at = datetime.now()
            quote.approved_by = user_id
        elif status_update.status == 'rejected':
            quote.rejection_reason = status_update.comments
        
        # 创建审批记录
        approval_record = ApprovalRecord(
            quote_id=quote_id,
            action=f"status_change:{old_status}->{status_update.status}",
            status=status_update.status,
            approver_id=user_id,
            comments=status_update.comments,
            processed_at=datetime.now()
        )
        self.db.add(approval_record)
        
        quote.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(quote)
        return quote

    def get_quote_statistics(self, user_id: Optional[int] = None) -> QuoteStatistics:
        """获取报价单统计信息"""
        query = self.db.query(Quote).filter(Quote.is_deleted == False)

        # 非管理员只能看到自己创建的报价单统计
        if user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.role not in ['admin', 'super_admin']:
                query = query.filter(Quote.created_by == user_id)
        
        # 简单统计各状态数量
        total = query.count()
        draft = query.filter(Quote.status == 'draft').count()
        pending = query.filter(Quote.status == 'pending').count()
        approved = query.filter(Quote.status == 'approved').count()
        rejected = query.filter(Quote.status == 'rejected').count()
        
        return QuoteStatistics(
            total=total,
            draft=draft,
            pending=pending,
            approved=approved,
            rejected=rejected
        )

    def get_approval_records(self, quote_id: int) -> List[ApprovalRecord]:
        """获取报价单审批记录"""
        return (
            self.db.query(ApprovalRecord)
            .filter(ApprovalRecord.quote_id == quote_id)
            .order_by(desc(ApprovalRecord.created_at))
            .all()
        )

    def submit_for_approval(self, quote_id: int, user_id: int) -> Optional[Quote]:
        """提交报价单到企业微信审批"""
        from .wecom_approval_service import WeComApprovalService
        
        quote = self.get_quote_by_id(quote_id)
        if not quote:
            return None
        
        if quote.status != 'draft':
            raise ValueError("只有草稿状态的报价单可以提交审批")
        
        # 使用企业微信审批服务
        wecom_service = WeComApprovalService(self.db)
        
        try:
            # 提交到企业微信审批
            sp_no = wecom_service.submit_quote_approval(quote_id, user_id)
            
            # 刷新报价单对象
            self.db.refresh(quote)
            return quote
            
        except Exception as e:
            # 如果企业微信审批失败，回退到本地状态更新
            print(f"企业微信审批提交失败，使用本地审批: {e}")
            
            status_update = QuoteStatusUpdate(
                status='pending',
                comments='提交本地审批（企业微信审批暂不可用）'
            )
            
            return self.update_quote_status(quote_id, status_update, user_id)

    def approve_quote(self, quote_id: int, approver_id: int, comments: str = "审批通过"):
        """批准报价单"""
        quote = self.get_quote_by_id(quote_id)
        if not quote:
            raise ValueError("报价单不存在")
        
        if quote.status != 'pending':
            raise ValueError("只有审批中的报价单可以批准")
        
        # 更新报价单状态
        self._sync_status_fields(quote, status='approved')
        quote.approved_by = approver_id
        quote.approved_at = datetime.utcnow()

        # 记录审批操作
        approval_record = ApprovalRecord(
            quote_id=quote_id,
            action='approve',
            status='approved',
            approver_id=approver_id,
            comments=comments,
            processed_at=datetime.utcnow()
        )
        self.db.add(approval_record)
        
        self.db.commit()
        self.db.refresh(quote)
        return quote

    def reject_quote(self, quote_id: int, approver_id: int, comments: str):
        """拒绝报价单"""
        quote = self.get_quote_by_id(quote_id)
        if not quote:
            raise ValueError("报价单不存在")
        
        if quote.status != 'pending':
            raise ValueError("只有审批中的报价单可以拒绝")
        
        # 更新报价单状态
        self._sync_status_fields(quote, status='rejected')
        quote.rejection_reason = comments

        # 记录审批操作
        approval_record = ApprovalRecord(
            quote_id=quote_id,
            action='reject',
            status='rejected',
            approver_id=approver_id,
            comments=comments,
            processed_at=datetime.utcnow()
        )
        self.db.add(approval_record)
        
        self.db.commit()
        self.db.refresh(quote)
        return quote
