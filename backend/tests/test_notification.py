#!/usr/bin/env python3
"""
测试企业微信消息通知
"""

import asyncio
import httpx
from app.services.wecom_integration import WeComApprovalIntegration
from app.database import get_db

async def test_direct_message():
    """直接调用企业微信消息API发送通知"""
    print("📱 测试企业微信消息通知")
    print("=" * 50)
    
    db = next(get_db())
    try:
        service = WeComApprovalIntegration(db)
        
        # 获取access_token
        print("1. 获取access_token...")
        access_token = await service.get_access_token()
        print(f"✅ Access token: {access_token[:20]}...")
        
        # 构建消息内容
        message_data = {
            "touser": "qixin",  # 接收人userid
            "msgtype": "textcard",
            "agentid": service.agent_id,
            "textcard": {
                "title": "📋 报价单审批通过",
                "description": f"""
<div class=\"gray\">报价单号：CIS-KS20250830002</div>
<div class=\"gray\">审批状态：✅ 已通过</div>
<div class=\"gray\">审批时间：2025-09-02 11:05</div>
<div class=\"normal\">您的报价单已通过审批，可以开始执行相关工作。</div>
                """,
                "url": "http://localhost:3000/quote-detail/31",
                "btntxt": "查看详情"
            }
        }
        
        # 发送消息
        print("2. 发送审批通过通知...")
        async with httpx.AsyncClient() as client:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            response = await client.post(url, json=message_data)
            result = response.json()
            
            if result.get('errcode') == 0:
                print("✅ 审批通过通知发送成功")
                print(f"📤 消息ID: {result.get('msgid')}")
            else:
                print(f"❌ 通知发送失败: {result.get('errmsg')} (错误码: {result.get('errcode')})")
                
        # 测试审批拒绝通知
        print("\n3. 测试审批拒绝通知...")
        reject_message = {
            "touser": "qixin",
            "msgtype": "textcard", 
            "agentid": service.agent_id,
            "textcard": {
                "title": "📋 报价单审批拒绝",
                "description": f"""
<div class=\"gray\">报价单号：测试报价单001</div>
<div class=\"gray\">审批状态：❌ 已拒绝</div>
<div class=\"gray\">拒绝原因：金额超出预算范围</div>
<div class=\"normal\">您的报价单未通过审批，请根据意见修改后重新提交。</div>
                """,
                "url": "http://localhost:3000/quotes",
                "btntxt": "修改报价"
            }
        }
        
        response = await client.post(url, json=reject_message)
        result = response.json()
        
        if result.get('errcode') == 0:
            print("✅ 审批拒绝通知发送成功")
        else:
            print(f"❌ 拒绝通知发送失败: {result.get('errmsg')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_direct_message())