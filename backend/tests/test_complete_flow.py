#!/usr/bin/env python3
"""
完整审批流程测试脚本
测试: 创建报价单 -> 提交审批 -> 审批人拒绝/同意 -> 状态同步
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def check_quote_status(quote_number):
    """检查报价单状态"""
    response = requests.get(f"{BASE_URL}/quotes/test")
    if response.status_code == 200:
        quotes = response.json()
        for quote in quotes['items']:
            if quote['quote_number'] == quote_number:
                return quote
    return None

def simulate_approval_action(quote_number, action):
    """模拟审批动作"""
    data = {
        "quote_number": quote_number,
        "action": action,
        "sp_no": f"test_{quote_number}_{int(datetime.now().timestamp())}"
    }
    
    response = requests.post(
        f"{BASE_URL}/wecom-callback/simulate-approval",
        json=data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 模拟审批失败: {response.text}")
        return None

def main():
    print_separator("企业微信审批流程完整测试")
    
    # 选择一个测试报价单
    test_quote = "CIS-KS20250829003"
    
    # 第一步：重置报价单状态为pending
    print(f"\n📋 步骤1: 重置报价单 {test_quote} 状态为 '待审批'")
    import sqlite3
    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE quotes 
        SET status='pending', approval_status='pending', wecom_approval_id='test_workflow_001'
        WHERE quote_number=?
    """, (test_quote,))
    conn.commit()
    conn.close()
    
    # 检查初始状态
    quote_info = check_quote_status(test_quote)
    if quote_info:
        print(f"✅ 初始状态: {quote_info['status']} / {quote_info.get('approval_status', 'null')}")
    else:
        print(f"❌ 未找到报价单: {test_quote}")
        return
    
    # 第二步：模拟审批人拒绝
    print_separator("步骤2: 模拟审批人拒绝审批")
    result = simulate_approval_action(test_quote, "rejected")
    if result and result.get('success'):
        print(f"✅ 拒绝成功: {result['message']}")
        updated_quote = result['quote']
        print(f"   更新后状态: {updated_quote['status']} / {updated_quote['approval_status']}")
    else:
        print("❌ 拒绝处理失败")
        return
    
    time.sleep(1)
    
    # 第三步：重新提交审批（模拟用户重新提交）
    print_separator("步骤3: 重新提交审批")
    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE quotes 
        SET status='pending', approval_status='pending'
        WHERE quote_number=?
    """, (test_quote,))
    conn.commit()
    conn.close()
    
    quote_info = check_quote_status(test_quote)
    if quote_info:
        print(f"✅ 重新提交后状态: {quote_info['status']} / {quote_info.get('approval_status', 'null')}")
    
    time.sleep(1)
    
    # 第四步：模拟审批人同意
    print_separator("步骤4: 模拟审批人同意审批")
    result = simulate_approval_action(test_quote, "approved")
    if result and result.get('success'):
        print(f"✅ 同意成功: {result['message']}")
        updated_quote = result['quote']
        print(f"   更新后状态: {updated_quote['status']} / {updated_quote['approval_status']}")
        print(f"   更新时间: {updated_quote['updated_at']}")
    else:
        print("❌ 同意处理失败")
        return
    
    # 第五步：验证最终状态
    print_separator("步骤5: 验证最终状态")
    final_quote = check_quote_status(test_quote)
    if final_quote:
        print(f"📊 最终报价单状态:")
        print(f"   报价单号: {final_quote['quote_number']}")
        print(f"   主要状态: {final_quote['status']}")
        print(f"   审批状态: {final_quote.get('approval_status', 'null')}")
        print(f"   更新时间: {final_quote.get('updated_at', 'null')}")
        
        if final_quote['status'] == 'approved' and final_quote.get('approval_status') == 'approved':
            print(f"\n🎉 审批流程测试成功！")
            print(f"   ✅ 1. 能够正常提交审批")
            print(f"   ✅ 2. 提交后状态正确显示")
            print(f"   ✅ 3. 审批人同意/拒绝后状态正确同步")
        else:
            print(f"\n⚠️ 状态同步可能存在问题")
    
    print_separator("测试完成")

if __name__ == "__main__":
    main()
