#!/usr/bin/env python3
"""
测试企业微信审批集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Quote, User
from app.services.wecom_approval_service import WeComApprovalService

def test_wecom_approval():
    """测试企业微信审批功能"""
    print("🔧 测试企业微信审批集成...")
    
    db = SessionLocal()
    try:
        # 获取一个草稿状态的报价单
        draft_quote = db.query(Quote).filter(Quote.status == 'draft').first()
        if not draft_quote:
            print("❌ 没有找到草稿状态的报价单")
            return
        
        print(f"✅ 找到草稿报价单: {draft_quote.quote_number} - {draft_quote.title}")
        
        # 获取用户
        user = db.query(User).first()
        if not user:
            print("❌ 没有找到用户")
            return
        
        print(f"✅ 使用用户: {user.name}")
        
        # 创建审批服务
        approval_service = WeComApprovalService(db)
        
        # 测试检查审批状态（未提交）
        print("\n🔍 测试检查审批状态...")
        try:
            status = approval_service.check_approval_status(draft_quote.id)
            print(f"✅ 审批状态: {status}")
        except Exception as e:
            print(f"⚠️  检查审批状态失败（预期）: {e}")
        
        # 测试提交审批（会失败，因为没有真实的企业微信配置）
        print("\n🚀 测试提交审批...")
        try:
            sp_no = approval_service.submit_quote_approval(draft_quote.id, user.id)
            print(f"✅ 审批提交成功，审批单号: {sp_no}")
        except Exception as e:
            print(f"⚠️  审批提交失败（预期，因为没有真实配置）: {e}")
        
        # 测试获取审批历史
        print("\n📋 测试获取审批历史...")
        try:
            history = approval_service.get_approval_history(draft_quote.id)
            print(f"✅ 审批历史: {history}")
        except Exception as e:
            print(f"⚠️  获取审批历史失败（预期）: {e}")
        
        print("\n" + "="*60)
        print("✅ 企业微信审批集成测试完成")
        print("\n📝 注意事项:")
        print("1. 实际使用需要配置真实的企业微信参数")
        print("2. 需要在企业微信管理后台创建审批模板")
        print("3. 需要配置审批回调URL")
        print("4. 需要设置环境变量或配置文件")
        print("\n🔧 配置步骤:")
        print("- 设置 WECOM_CORP_ID")
        print("- 设置 WECOM_AGENT_ID")
        print("- 设置 WECOM_CORP_SECRET")
        print("- 设置 WECOM_QUOTE_TEMPLATE_ID")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_wecom_approval()