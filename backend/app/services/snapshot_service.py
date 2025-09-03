from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Quote, QuoteSnapshot, EffectiveQuote
from .rules_loader import get_rules
import logging

logger = logging.getLogger(__name__)

class SnapshotService:
    """报价单快照服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rules = get_rules()
    
    def create_snapshot(
        self, 
        quote: Quote, 
        template_id: str, 
        approvers: List[str], 
        creator_id: int = None
    ) -> QuoteSnapshot:
        """
        创建报价单快照
        
        Args:
            quote: 报价单对象
            template_id: 审批模板ID
            approvers: 审批人列表
            creator_id: 创建者ID
            
        Returns:
            QuoteSnapshot: 创建的快照对象
        """
        try:
            # 使用模型的类方法创建快照
            snapshot = QuoteSnapshot.from_quote(
                quote=quote,
                template_id=template_id,
                approvers=approvers,
                creator_id=creator_id
            )
            
            # 保存到数据库
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            logger.info(f"创建快照成功: quote_id={quote.id}, snapshot_id={snapshot.id}, hash={snapshot.hash}")
            return snapshot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建快照失败: quote_id={quote.id}, error={e}")
            raise
    
    def get_snapshot(self, snapshot_id: int) -> Optional[QuoteSnapshot]:
        """获取快照详情"""
        return self.db.query(QuoteSnapshot).filter(
            QuoteSnapshot.id == snapshot_id
        ).first()
    
    def get_snapshots_by_quote(self, quote_id: int) -> List[QuoteSnapshot]:
        """获取报价单的所有快照"""
        return self.db.query(QuoteSnapshot).filter(
            QuoteSnapshot.quote_id == quote_id
        ).order_by(QuoteSnapshot.created_at.desc()).all()
    
    def verify_snapshot_integrity(self, snapshot_id: int) -> bool:
        """验证快照数据完整性"""
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            return False
        
        try:
            # 重新计算哈希值并对比
            calculated_hash = snapshot.calc_hash()
            return calculated_hash == snapshot.hash
        except Exception as e:
            logger.error(f"验证快照完整性失败: snapshot_id={snapshot_id}, error={e}")
            return False
    
    def create_effective_quote(
        self, 
        quote_id: int, 
        snapshot_id: int, 
        creator_id: int = None
    ) -> EffectiveQuote:
        """
        创建生效报价单
        
        Args:
            quote_id: 报价单ID
            snapshot_id: 快照ID
            creator_id: 创建者ID
            
        Returns:
            EffectiveQuote: 生效报价单对象
        """
        try:
            # 获取当前最新版本号
            latest_effective = self.db.query(EffectiveQuote).filter(
                EffectiveQuote.quote_id == quote_id
            ).order_by(EffectiveQuote.created_at.desc()).first()
            
            # 计算下一个版本号
            if latest_effective:
                try:
                    current_version = float(latest_effective.version)
                    next_version = str(current_version + 0.1)
                except (ValueError, TypeError):
                    next_version = "1.1"
            else:
                next_version = "1.0"
            
            # 创建生效报价单
            effective_quote = EffectiveQuote(
                quote_id=quote_id,
                snapshot_id=snapshot_id,
                version=next_version,
                created_by=creator_id,
                effective_at=datetime.utcnow()
            )
            
            self.db.add(effective_quote)
            self.db.commit()
            self.db.refresh(effective_quote)
            
            logger.info(f"创建生效报价单成功: quote_id={quote_id}, version={next_version}")
            return effective_quote
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建生效报价单失败: quote_id={quote_id}, error={e}")
            raise
    
    def get_effective_quotes(self, quote_id: int) -> List[EffectiveQuote]:
        """获取报价单的所有生效版本"""
        return self.db.query(EffectiveQuote).filter(
            EffectiveQuote.quote_id == quote_id
        ).order_by(EffectiveQuote.created_at.desc()).all()
    
    def get_latest_effective_quote(self, quote_id: int) -> Optional[EffectiveQuote]:
        """获取最新的生效报价单"""
        return self.db.query(EffectiveQuote).filter(
            EffectiveQuote.quote_id == quote_id
        ).order_by(EffectiveQuote.created_at.desc()).first()
    
    def cleanup_old_snapshots(self, quote_id: int, keep_count: int = 10) -> int:
        """
        清理旧快照，保留最新的N个
        
        Args:
            quote_id: 报价单ID
            keep_count: 保留数量
            
        Returns:
            int: 删除的快照数量
        """
        try:
            # 获取所有快照，按创建时间倒序
            snapshots = self.db.query(QuoteSnapshot).filter(
                QuoteSnapshot.quote_id == quote_id
            ).order_by(QuoteSnapshot.created_at.desc()).all()
            
            if len(snapshots) <= keep_count:
                return 0
            
            # 删除超出保留数量的快照
            snapshots_to_delete = snapshots[keep_count:]
            deleted_count = 0
            
            for snapshot in snapshots_to_delete:
                # 检查是否有生效报价单引用此快照
                effective_count = self.db.query(EffectiveQuote).filter(
                    EffectiveQuote.snapshot_id == snapshot.id
                ).count()
                
                if effective_count == 0:
                    self.db.delete(snapshot)
                    deleted_count += 1
            
            self.db.commit()
            logger.info(f"清理旧快照完成: quote_id={quote_id}, deleted={deleted_count}")
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"清理旧快照失败: quote_id={quote_id}, error={e}")
            return 0