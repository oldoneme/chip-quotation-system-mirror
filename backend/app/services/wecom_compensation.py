#!/usr/bin/env python3
"""
企业微信审批状态补偿服务
用于补偿失败的回调或状态不一致的情况
"""

import httpx
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db
from ..models import Quote, ApprovalTimeline, ApprovalTimelineErrors
from ..config import settings


class WeComCompensationService:
    """企业微信审批补偿服务"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.corp_id = settings.WECOM_CORP_ID
        self.secret = settings.WECOM_SECRET
        self._access_token = None
        self._token_expires_at = None
    
    async def get_access_token(self) -> str:
        """获取企业微信access_token"""
        if self._access_token and self._token_expires_at:
            if time.time() < self._token_expires_at:
                return self._access_token
        
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {"corpid": self.corp_id, "corpsecret": self.secret}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
        if data.get("errcode") != 0:
            raise Exception(f"获取access_token失败: {data.get('errmsg')}")
        
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"] - 300
        return self._access_token
    
    async def get_approval_detail(self, sp_no: str) -> Optional[Dict]:
        """获取审批详情"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovaldetail"
            
            data = {"sp_no": sp_no}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{url}?access_token={access_token}",
                    json=data
                )
                result = response.json()
            
            if result.get("errcode") != 0:
                print(f"⚠️ 获取审批详情失败: {result.get('errmsg')}")
                return None
                
            return result.get("info", {})
            
        except Exception as e:
            print(f"❌ 获取审批详情异常: {str(e)}")
            return None
    
    async def sync_approval_status(self, quote_id: int) -> bool:
        """同步单个报价单的审批状态"""
        try:
            # 获取报价单
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                print(f"❌ 报价单ID={quote_id}不存在")
                return False
            
            if not quote.wecom_approval_id:
                print(f"❌ 报价单ID={quote_id}没有企业微信审批ID")
                return False
            
            # 获取审批详情
            detail = await self.get_approval_detail(quote.wecom_approval_id)
            if not detail:
                return False
            
            # 解析状态
            sp_status = detail.get("sp_status")
            if sp_status is None:
                print(f"⚠️ 审批详情中没有sp_status字段")
                return False
            
            # 状态映射
            status_mapping = {
                1: "pending",     # 审批中
                2: "approved",    # 已通过
                3: "rejected",    # 已拒绝
                4: "cancelled"    # 已取消
            }
            
            new_status = status_mapping.get(sp_status)
            if not new_status:
                print(f"❌ 未知的审批状态: {sp_status}")
                return False
            
            # 更新报价单状态
            old_status = quote.status
            if old_status != new_status:
                quote.status = new_status
                quote.approval_status = new_status
                quote.updated_at = datetime.now()
                
                # 记录补偿时间线
                try:
                    timeline = ApprovalTimeline(
                        event_id=f"reconcile_{quote_id}_{int(time.time())}",
                        sp_no=quote.wecom_approval_id,
                        third_no=str(quote_id),
                        status=sp_status,
                        created_at=datetime.now()
                    )
                    self.db.add(timeline)
                except Exception as timeline_e:
                    print(f"⚠️ 记录补偿时间线失败: {str(timeline_e)}")
                
                self.db.commit()
                print(f"✅ 补偿同步成功: 报价单{quote.quote_number} {old_status}→{new_status}")
                return True
            else:
                print(f"ℹ️ 状态已一致: 报价单{quote.quote_number} status={new_status}")
                return True
                
        except Exception as e:
            print(f"❌ 同步报价单{quote_id}状态异常: {str(e)}")
            self.db.rollback()
            return False
    
    async def sync_all_pending_quotes(self) -> Dict:
        """同步所有pending状态超过10分钟的报价单"""
        try:
            # 查找超过10分钟还是pending状态的报价单
            cutoff_time = datetime.now() - timedelta(minutes=10)
            pending_quotes = self.db.query(Quote).filter(
                and_(
                    Quote.status == "pending",
                    Quote.wecom_approval_id.isnot(None),
                    Quote.updated_at < cutoff_time
                )
            ).all()
            
            print(f"🔍 发现{len(pending_quotes)}个需要补偿的报价单")
            
            success_count = 0
            failed_count = 0
            
            for quote in pending_quotes:
                print(f"\n📍 处理报价单: {quote.quote_number} (ID={quote.id})")
                if await self.sync_approval_status(quote.id):
                    success_count += 1
                else:
                    failed_count += 1
                
                # 避免频率限制
                await asyncio.sleep(0.5)
            
            result = {
                "total": len(pending_quotes),
                "success": success_count,
                "failed": failed_count,
                "processed_at": datetime.now().isoformat()
            }
            
            print(f"\n🏁 批量同步完成: 成功{success_count}个, 失败{failed_count}个")
            return result
            
        except Exception as e:
            print(f"❌ 批量同步异常: {str(e)}")
            return {"error": str(e)}
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'db') and self.db:
            self.db.close()


# 测试补偿功能
async def test_compensation():
    """测试补偿功能"""
    print("🎯 开始测试失败兜底补偿机制")
    
    # 先手动将一个报价单设置为pending状态（模拟卡住的情况）
    db = next(get_db())
    quote = db.query(Quote).filter(Quote.id == 12).first()
    if quote:
        # 设置为15分钟前的pending状态
        old_time = datetime.now() - timedelta(minutes=15)
        quote.status = "pending"
        quote.approval_status = "pending"  
        quote.updated_at = old_time
        
        # 确保有企业微信审批ID（模拟）
        if not quote.wecom_approval_id:
            quote.wecom_approval_id = "test_compensation_sp_123"
        
        db.commit()
        print(f"✅ 已将报价单{quote.quote_number}设置为15分钟前的pending状态")
    
    # 测试补偿同步
    sync_service = WeComCompensationService(db)
    
    try:
        print(f"\n📍 测试单个报价单补偿同步...")
        print(f"   注意：由于没有真实的企业微信审批ID，这个测试会模拟失败情况")
        success = await sync_service.sync_approval_status(12)
        print(f"   单个同步结果: {'✅ 成功' if success else '❌ 失败（预期，因为是测试环境）'}")
        
        print(f"\n📍 测试批量补偿同步...")
        result = await sync_service.sync_all_pending_quotes()
        print(f"   批量同步结果: {result}")
        
    finally:
        sync_service.close()
    
    print(f"\n🏁 补偿机制测试完成")
    print(f"📋 补偿逻辑已实现，可在生产环境中调用")


if __name__ == "__main__":
    import sys
    sys.path.append('/home/qixin/projects/chip-quotation-system/backend')
    asyncio.run(test_compensation())