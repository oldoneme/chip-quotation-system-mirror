#!/usr/bin/env python3
"""
创建新报价单并测试提交审批
"""

import requests
import json

def create_quote():
    """创建测试报价单"""
    print("📝 创建测试报价单...")

    create_data = {
        "quote_number": "TEST-SYNC-001",
        "title": "状态同步测试",
        "quote_type": "tooling",
        "customer_name": "测试客户",
        "customer_contact": "测试联系人",
        "customer_phone": "13800138000",
        "customer_email": "test@example.com",
        "total_amount": 100.0,
        "items": [
            {
                "item_name": "测试项目",
                "item_description": "用于测试状态同步",
                "quantity": 1,
                "unit_price": 100.0,
                "total_price": 100.0
            }
        ]
    }

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/quotes/",
            json=create_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 201:
            quote_data = response.json()
            quote_id = quote_data["id"]
            print(f"✅ 创建成功，报价单ID: {quote_id}")
            return quote_id
        else:
            print(f"❌ 创建失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ 创建异常: {str(e)}")
        return None

def submit_approval(quote_id):
    """提交审批"""
    print(f"\n🚀 提交审批 - 报价单ID: {quote_id}")

    try:
        response = requests.post(
            f"http://localhost:8000/api/v2/approval/{quote_id}/operate",
            json={
                "action": "submit",
                "comments": "测试状态同步",
                "channel": "auto"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"状态码: {response.status_code}")
        if response.text:
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result.get('success', False)
            except:
                print(f"响应文本: {response.text}")
                return False

    except Exception as e:
        print(f"❌ 提交异常: {str(e)}")
        return False

def check_quote_status(quote_id):
    """检查报价单状态"""
    print(f"\n🔍 检查报价单状态 - ID: {quote_id}")

    import sqlite3
    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id, quote_number, status, approval_status
            FROM quotes
            WHERE id = ?
        ''', (quote_id,))
        result = cursor.fetchone()

        if result:
            quote_id, quote_number, status, approval_status = result
            print(f"   报价单: {quote_number}")
            print(f"   状态: {status}")
            print(f"   审批状态: {approval_status}")

            if status == approval_status == "pending":
                print(f"   ✅ 状态同步正确")
                return True
            else:
                print(f"   ❌ 状态不同步 - status: {status}, approval_status: {approval_status}")
                return False
        else:
            print(f"   ❌ 报价单不存在")
            return False

    except Exception as e:
        print(f"   ❌ 检查失败: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("🧪 状态同步完整测试")
    print("=" * 50)

    # 步骤1: 创建报价单
    quote_id = create_quote()
    if not quote_id:
        print("❌ 测试失败 - 无法创建报价单")
        return

    # 步骤2: 提交审批
    success = submit_approval(quote_id)
    if not success:
        print("❌ 测试失败 - 提交审批失败")

    # 步骤3: 检查状态同步
    synced = check_quote_status(quote_id)

    print("\n" + "=" * 50)
    if synced:
        print("🎉 状态同步测试通过！")
    else:
        print("⚠️ 状态同步存在问题")

if __name__ == "__main__":
    main()