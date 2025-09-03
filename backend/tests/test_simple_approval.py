#!/usr/bin/env python3
"""
简单的企业微信审批测试脚本
测试基本的审批提交功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.services.wecom_integration import WeComApprovalIntegration
from app.models import Quote

async def test_approval_submission():
    """测试审批提交功能"""
    print("🧪 开始测试企业微信审批提交...")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 创建集成服务实例
        wecom_service = WeComApprovalIntegration(db)
        
        # 获取第一个报价单进行测试
        quote = db.query(Quote).first()
        if not quote:
            print("❌ 没有找到报价单，请先创建一个报价单")
            return
        
        print(f"📋 使用报价单: {quote.quote_number} (ID: {quote.id})")
        print(f"👤 创建人: {quote.creator.name if quote.creator else 'Unknown'}")
        print(f"🏢 客户: {quote.customer_name}")
        
        # 测试获取access_token
        print("\n🔑 测试获取access_token...")
        try:
            access_token = await wecom_service.get_access_token()
            print(f"✅ 获取access_token成功: {access_token[:20]}...")
        except Exception as e:
            print(f"❌ 获取access_token失败: {e}")
            return
        
        # 测试提交审批
        print("\n📤 测试提交审批...")
        try:
            result = await wecom_service.submit_quote_approval(quote.id)
            print(f"✅ 审批提交成功!")
            print(f"📝 审批单号: {result.get('sp_no')}")
            print(f"💬 消息: {result.get('message')}")
            
            # 检查报价单状态更新
            db.refresh(quote)
            print(f"🔄 报价单审批状态: {quote.approval_status}")
            print(f"🆔 企业微信审批ID: {quote.wecom_approval_id}")
            
        except Exception as e:
            print(f"❌ 提交审批失败: {e}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    finally:
        db.close()

async def test_get_approval_detail():
    """测试获取审批详情"""
    print("\n🔍 测试获取审批详情...")
    
    db = next(get_db())
    try:
        wecom_service = WeComApprovalIntegration(db)
        
        # 查找有审批ID的报价单
        quote = db.query(Quote).filter(Quote.wecom_approval_id.isnot(None)).first()
        if not quote:
            print("❌ 没有找到有审批ID的报价单")
            return
        
        print(f"📋 查询审批单: {quote.wecom_approval_id}")
        
        try:
            detail = await wecom_service.get_approval_detail(quote.wecom_approval_id)
            print("✅ 获取审批详情成功:")
            
            info = detail.get("info", {})
            print(f"📊 状态: {info.get('sp_status')}")
            print(f"📝 申请人: {info.get('applyer', {}).get('userid')}")
            print(f"🕒 申请时间: {info.get('apply_time')}")
            
        except Exception as e:
            print(f"❌ 获取审批详情失败: {e}")
            
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 企业微信审批集成测试 ===")
    
    # 运行基本测试
    asyncio.run(test_approval_submission())
    
    # 运行详情查询测试
    asyncio.run(test_get_approval_detail())
    
    print("\n🏁 测试完成")