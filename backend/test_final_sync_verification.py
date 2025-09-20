#!/usr/bin/env python3
"""
最终同步验证测试：创建有企业微信审批ID的报价单并测试同步
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Quote, QuoteItem
import sqlite3
import requests

def create_test_quote_with_wecom_id():
    """创建带有企业微信审批ID的测试报价单"""
    print("📝 创建带企业微信审批ID的测试报价单...")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 生成报价单编号
        quote_number = f"CIS-KS{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 创建报价单，设置为pending状态，并添加企业微信审批ID
        cursor.execute('''
            INSERT INTO quotes
            (quote_number, title, customer_name, customer_contact, customer_phone, customer_email,
             total_amount, status, approval_status, wecom_approval_id, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            quote_number,
            "同步测试报价单",
            "测试客户",
            "测试联系人",
            "13800138000",
            "test@example.com",
            1000.00,
            "pending",  # 设置为pending状态
            "pending",
            f"SYNC_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",  # 企业微信审批ID
            1,
            datetime.utcnow()
        ))

        quote_id = cursor.lastrowid

        # 添加报价项目
        cursor.execute('''
            INSERT INTO quote_items
            (quote_id, item_name, item_description, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            quote_id,
            "测试项目",
            "用于测试同步功能",
            1,
            1000.00,
            1000.00
        ))

        conn.commit()

        print(f"✅ 创建成功: {quote_number} (ID: {quote_id})")

        # 获取并显示完整信息
        cursor.execute('SELECT wecom_approval_id FROM quotes WHERE id = ?', (quote_id,))
        wecom_id = cursor.fetchone()[0]
        print(f"   企业微信审批ID: {wecom_id}")

        return quote_id, quote_number

    except Exception as e:
        print(f"❌ 创建测试报价单失败: {str(e)}")
        return None, None
    finally:
        conn.close()

def test_web_approval_with_sync(quote_id, quote_number):
    """测试网页端审批同步功能"""
    print(f"\n🔄 测试网页端审批同步功能")
    print(f"报价单: {quote_number} (ID: {quote_id})")

    # 检查初始状态
    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM approval_records WHERE quote_id = ?', (quote_id,))
    initial_count = cursor.fetchone()[0]
    print(f"初始审批记录数: {initial_count}")

    conn.close()

    # 执行网页端审批操作
    print(f"\n🖥️ 执行网页端批准操作...")
    try:
        response = requests.post(
            f"http://localhost:8000/api/v1/wecom-approval/approve/{quote_id}",
            json={"comments": "测试网页端批准，验证企业微信同步"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"API响应状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"API响应: {result.get('message', 'N/A')}")
        else:
            print(f"API错误: {response.text}")
            return False

    except Exception as e:
        print(f"API请求异常: {str(e)}")
        return False

    # 检查同步结果
    print(f"\n📊 检查同步结果...")
    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM approval_records WHERE quote_id = ?', (quote_id,))
    final_count = cursor.fetchone()[0]
    print(f"操作后审批记录数: {final_count}")

    # 查看最新的审批记录
    cursor.execute('''
        SELECT action, status, operation_channel, wecom_sp_no, comments, created_at
        FROM approval_records
        WHERE quote_id = ?
        ORDER BY created_at DESC
        LIMIT 2
    ''', (quote_id,))
    recent_records = cursor.fetchall()

    print(f"\n📜 最新审批记录:")
    sync_found = False
    for i, record in enumerate(recent_records, 1):
        action, status, channel, wecom_sp_no, comments, created_at = record
        print(f"   {i}. 动作: {action}, 状态: {status}, 渠道: {channel}")
        print(f"      企业微信编号: {wecom_sp_no}, 时间: {created_at}")
        print(f"      备注: {comments}")

        if channel and 'web_sync_to_wecom' in str(channel):
            sync_found = True
            print(f"      ✅ 发现同步标记!")

    # 检查报价单最终状态
    cursor.execute('SELECT status, approval_status FROM quotes WHERE id = ?', (quote_id,))
    final_status = cursor.fetchone()
    if final_status:
        print(f"\n📋 报价单最终状态: {final_status[0]}, 审批状态: {final_status[1]}")

    conn.close()

    if sync_found:
        print(f"\n✅ 同步功能正常工作!")
        return True
    else:
        print(f"\n⚠️ 没有发现同步标记，检查日志...")
        return False

if __name__ == "__main__":
    print("🧪 最终同步验证测试")

    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务无法访问")
            exit(1)
    except Exception as e:
        print(f"❌ 后端服务连接失败: {str(e)}")
        exit(1)

    # 创建测试报价单
    quote_id, quote_number = create_test_quote_with_wecom_id()
    if not quote_id:
        print("❌ 无法创建测试报价单")
        exit(1)

    # 测试同步功能
    success = test_web_approval_with_sync(quote_id, quote_number)

    if success:
        print(f"\n🎉 测试成功! 网页端审批同步功能正常工作")
        print(f"\n💡 修复总结:")
        print(f"   1. 访问控制: 使用三段兜底认证，支持不同用户角色")
        print(f"   2. 状态同步: 网页端操作标记'web_sync_to_wecom'并发送通知")
        print(f"   3. 权限管理: 审批权限根据用户角色动态判断")
    else:
        print(f"\n❌ 测试失败，需要进一步调试")