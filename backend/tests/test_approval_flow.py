#!/usr/bin/env python3
"""
完整审批流程测试
测试从前端提交到企业微信审批的完整流程
"""

import asyncio
import os
import httpx
from datetime import datetime

# 配置信息
TEST_CONFIG = {
    "api_base": "http://localhost:8000/api/v1",
    "quote_id": 30,
    "approver_userid": "test_user",  # 您可以改为实际的企业微信用户ID
}


def get_auth_headers():
    token = os.getenv("CHIP_QUOTE_AUTH_TOKEN")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def print_auth_required(test_name):
    print(f"⚠️  {test_name} 需要认证 token，已跳过受保护请求")
    print("   请先设置环境变量: export CHIP_QUOTE_AUTH_TOKEN=<token>")

async def test_quote_detail():
    """测试1: 获取报价单详情"""
    print("📋 测试1: 获取报价单详情")
    print("-" * 40)

    headers = get_auth_headers()
    if headers is None:
        print_auth_required("报价单详情接口")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TEST_CONFIG['api_base']}/quotes/detail/CIS-KS20250830001",
                headers=headers,
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 报价单获取成功")
                print(f"   报价单号: {data.get('quote_number')}")
                print(f"   客户名称: {data.get('customer_name')}")
                print(f"   报价金额: ¥{data.get('total_amount', 0):.2f}")
                print(f"   当前状态: {data.get('status')}")
                return True
            else:
                print(f"❌ 获取失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

async def test_submit_approval():
    """测试2: 提交审批申请"""
    print("\n📋 测试2: 提交审批申请")
    print("-" * 40)
    
    approval_data = {
        "approver_userid": TEST_CONFIG["approver_userid"],
        "urgency": "normal",
        "notes": "完整流程测试 - 请审批"
    }

    headers = get_auth_headers()
    if headers is None:
        print_auth_required("审批提交接口")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TEST_CONFIG['api_base']}/quote-approval/submit/{TEST_CONFIG['quote_id']}",
                json=approval_data,
                headers=headers,
                timeout=30.0
            )
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 审批提交成功！")
                print(f"   消息: {result.get('message')}")
                print(f"   审批ID: {result.get('approval_id')}")
                print(f"   通知发送: {result.get('notification_sent')}")
                return True
            else:
                result = response.json()
                error_detail = result.get("detail", "未知错误")
                print(f"❌ 审批提交失败")
                print(f"   错误信息: {error_detail}")
                
                # 分析错误类型并提供建议
                if "60020" in error_detail:
                    print("\n💡 IP白名单问题:")
                    print("   需要在企业微信后台添加IP: 222.92.137.26")
                elif "template" in error_detail.lower():
                    print("\n💡 模板问题:")
                    print("   请检查审批模板ID是否正确")
                elif "access_token" in error_detail.lower():
                    print("\n💡 认证问题:")
                    print("   请检查企业微信配置信息")
                
                return False
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

async def test_approval_history():
    """测试3: 查看审批历史"""
    print("\n📋 测试3: 查看审批历史")
    print("-" * 40)

    headers = get_auth_headers()
    if headers is None:
        print_auth_required("审批历史接口")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TEST_CONFIG['api_base']}/wecom-approval/history/{TEST_CONFIG['quote_id']}",
                headers=headers,
            )
            
            if response.status_code == 200:
                history = response.json()
                print(f"✅ 历史记录获取成功")
                print(f"   记录数量: {len(history)}")
                
                if history:
                    print("   最近记录:")
                    for i, record in enumerate(history[:3]):
                        print(f"     {i+1}. {record.get('action')} - {record.get('comments', 'No comments')}")
                
                return True
            else:
                print(f"❌ 获取失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

async def test_frontend_integration():
    """测试4: 前端集成验证"""
    print("\n📋 测试4: 前端集成验证")
    print("-" * 40)
    
    # 检查前端是否正在运行
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3000", timeout=5.0)
            
            if response.status_code == 200:
                print("✅ 前端服务运行正常")
                print("🌐 可访问地址:")
                print("   - 报价列表: http://localhost:3000/quotes")
                print("   - 报价详情: http://localhost:3000/quote-detail/30")
                print("   - 报价详情: http://localhost:3000/quote-detail/CIS-KS20250830001")
                return True
            else:
                print(f"⚠️  前端响应异常: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 前端连接失败: {e}")
        print("💡 请确保前端服务正在运行: npm start")
        return False

async def main():
    """主测试流程"""
    print("=" * 60)
    print("企业微信审批完整流程测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"测试配置:")
    print(f"  - 报价单ID: {TEST_CONFIG['quote_id']}")
    print(f"  - 审批人ID: {TEST_CONFIG['approver_userid']}")
    print(f"  - API地址: {TEST_CONFIG['api_base']}")
    print("=" * 60)
    
    # 执行测试
    results = []
    results.append(await test_quote_detail())
    results.append(await test_submit_approval())
    results.append(await test_approval_history())
    results.append(await test_frontend_integration())
    
    # 测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！审批系统集成成功！")
        print("\n📋 下一步可以:")
        print("1. 在前端界面测试提交审批")
        print("2. 检查企业微信是否收到审批通知")
        print("3. 测试审批流程的完整性")
    else:
        print("⚠️  部分测试失败，需要解决以下问题:")
        
        if not results[0]:
            print("- 报价单数据获取问题")
        if not results[1]:
            print("- 审批提交功能问题（可能是IP白名单）")
        if not results[2]:
            print("- 审批历史功能问题")
        if not results[3]:
            print("- 前端服务问题")
    
    print("\n🔍 如需调试，请查看:")
    print("- 后端日志: uvicorn输出")
    print("- 前端日志: 浏览器开发者工具")
    print("- 企业微信日志: 管理后台")

if __name__ == "__main__":
    asyncio.run(main())
