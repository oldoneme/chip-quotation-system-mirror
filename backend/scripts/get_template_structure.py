#!/usr/bin/env python3
"""
获取企业微信审批模板的真实结构
用于解决字段ID映射问题
"""

import asyncio
import sys
import os
import httpx
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db
from app.services.wecom_integration import WeComApprovalIntegration

async def get_template_structure():
    """获取审批模板详细结构"""
    print("📋 获取企业微信审批模板结构...")
    
    db = next(get_db())
    
    try:
        wecom_service = WeComApprovalIntegration(db)
        
        # 获取access_token
        access_token = await wecom_service.get_access_token()
        print(f"✅ 获取access_token成功: {access_token[:20]}...")
        
        # 获取模板详情API
        template_id = wecom_service.approval_template_id
        url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/gettemplatedetail?access_token={access_token}"
        
        data = {"template_id": template_id}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            result = response.json()
        
        if result.get("errcode") == 0:
            print("✅ 获取模板结构成功")
            print(f"📝 模板ID: {template_id}")
            
            template_names = result.get("template_names", [])
            template_content = result.get("template_content", {})
            
            print(f"\n📄 模板名称: {template_names}")
            print(f"📋 模板内容:")
            
            controls = template_content.get("controls", [])
            print(f"🎛️  控件总数: {len(controls)}")
            
            for i, control in enumerate(controls):
                print(f"\n--- 控件 {i+1} ---")
                print(f"🆔 ID: {control.get('id')}")
                print(f"📝 属性: {control.get('property', {})}")
                print(f"🎨 控件类型: {control.get('property', {}).get('control')}")
                print(f"📜 标题: {control.get('property', {}).get('title')}")
                print(f"🔧 配置: {control.get('config', {})}")
                
            return controls
        else:
            print(f"❌ 获取模板结构失败: {result.get('errmsg')}")
            return None
            
    except Exception as e:
        print(f"❌ 获取过程中发生错误: {e}")
        return None
    finally:
        db.close()

async def create_correct_approval_data():
    """基于真实模板结构创建正确的审批数据"""
    print("\n🔧 基于真实模板创建审批数据...")
    
    controls = await get_template_structure()
    if not controls:
        print("❌ 无法获取模板结构，无法继续")
        return
    
    # 模拟报价单数据
    quote_data = {
        "quote_type": "标准报价",
        "quote_number": "TEST-001",
        "customer_name": "测试客户",
        "description": "测试描述",
        "total_amount": 1000.00,
        "detail_url": "https://example.com/quote-detail/1"
    }
    
    print(f"\n✨ 基于 {len(controls)} 个控件创建审批数据:")
    
    contents = []
    for i, control in enumerate(controls):
        control_id = control.get('id')
        control_type = control.get('property', {}).get('control')
        title = control.get('property', {}).get('title')
        
        print(f"🎛️  控件{i+1}: {title} (ID: {control_id}, 类型: {control_type})")
        
        # 根据控件类型和标题推测应该填入什么数据
        if control_type == "Text":
            if "报价类型" in str(title) or "类型" in str(title):
                value = quote_data["quote_type"]
            elif "报价单号" in str(title) or "单号" in str(title):
                value = quote_data["quote_number"]  
            elif "客户" in str(title):
                value = quote_data["customer_name"]
            elif "描述" in str(title) or "备注" in str(title):
                value = quote_data["description"]
            elif "金额" in str(title) or "价格" in str(title):
                value = f"¥{quote_data['total_amount']:.2f}"
            elif "链接" in str(title) or "地址" in str(title):
                value = quote_data["detail_url"]
            else:
                value = f"控件{i+1}的值"
                
            contents.append({
                "control": "Text",
                "id": control_id,
                "value": {"text": value}
            })
            
        elif control_type == "File":
            # File控件暂时留空
            contents.append({
                "control": "File", 
                "id": control_id,
                "value": {"files": []}
            })
            
    print(f"\n📋 生成的审批数据结构:")
    for content in contents:
        print(f"  - {content['control']}: {content['id']} = {content['value']}")
        
    return contents

if __name__ == "__main__":
    print("=== 企业微信审批模板结构分析 ===")
    
    # 获取模板结构
    asyncio.run(create_correct_approval_data())
    
    print("\n🏁 分析完成")