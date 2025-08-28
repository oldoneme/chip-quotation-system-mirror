"""
报价单服务层
处理报价单相关的业务逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from ..models import Quote, QuoteItem, ApprovalRecord, User
from ..schemas import (
    QuoteCreate, QuoteUpdate, QuoteFilter, 
    QuoteStatusUpdate, ApprovalRecordCreate,
    QuoteStatistics
)


class QuoteService:
    """报价单服务类"""

    def __init__(self, db: Session):
        self.db = db

    def generate_quote_number(self) -> str:
        """生成报价单号"""
        # 获取当前年月
        now = datetime.now()
        year_month = now.strftime("%Y%m")
        
        # 查找当月最大编号
        latest_quote = (
            self.db.query(Quote)
            .filter(Quote.quote_number.like(f"QT{year_month}%"))
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
        
        return f"QT{year_month}{seq:03d}"

    def create_quote(self, quote_data: QuoteCreate, user_id: int) -> Quote:
        """创建报价单"""
        # 生成报价单号
        quote_number = self.generate_quote_number()
        
        # 创建报价单主记录
        quote_dict = quote_data.model_dump(exclude={'items'})
        quote_dict.update({
            'quote_number': quote_number,
            'status': 'draft',
            'created_by': user_id
        })
        
        quote = Quote(**quote_dict)
        self.db.add(quote)
        self.db.flush()  # 获取ID但不提交
        
        # 创建报价明细
        for item_data in quote_data.items:
            item_dict = item_data.model_dump()
            item_dict['quote_id'] = quote.id
            item = QuoteItem(**item_dict)
            self.db.add(item)
        
        self.db.commit()
        self.db.refresh(quote)
        return quote

    def get_quote_by_id(self, quote_id: int) -> Optional[Quote]:
        """根据ID获取报价单"""
        return self.db.query(Quote).filter(Quote.id == quote_id).first()

    def get_quote_by_number(self, quote_number: str) -> Optional[Quote]:
        """根据报价单号获取报价单"""
        return self.db.query(Quote).filter(Quote.quote_number == quote_number).first()

    def get_quotes(self, filter_params: QuoteFilter, user_id: Optional[int] = None):
        """获取报价单列表"""
        # 构建基础查询
        base_filters = []
        
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
            # 如果没有指定创建人且提供了用户ID，则只显示该用户的报价单
            # 管理员可以看到所有报价单
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.role not in ['admin', 'super_admin']:
                base_filters.append(Quote.created_by == user_id)
        
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
        data_query = self.db.query(Quote)
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
        
        # 检查状态：只有草稿状态可以编辑
        if quote.status != 'draft':
            raise ValueError("只有草稿状态的报价单可以编辑")
        
        # 更新报价单字段
        update_data = quote_data.model_dump(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(quote, field, value)
        
        # 更新报价明细
        if quote_data.items is not None:
            # 删除旧的明细项
            self.db.query(QuoteItem).filter(QuoteItem.quote_id == quote_id).delete()
            
            # 添加新的明细项
            for item_data in quote_data.items:
                item_dict = item_data.model_dump(exclude_unset=True)
                item_dict['quote_id'] = quote_id
                item = QuoteItem(**item_dict)
                self.db.add(item)
        
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
        if not user or (quote.created_by != user_id and user.role not in ['admin', 'super_admin']):
            raise PermissionError("无权限删除此报价单")
        
        # 检查状态：只有草稿状态可以删除
        if quote.status != 'draft':
            raise ValueError("只有草稿状态的报价单可以删除")
        
        # 删除关联的明细项和审批记录会通过级联删除自动处理
        self.db.delete(quote)
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
        quote.status = status_update.status
        
        # 根据状态更新相应字段
        if status_update.status == 'pending':
            quote.submitted_at = datetime.now()
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
        query = self.db.query(Quote)
        
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