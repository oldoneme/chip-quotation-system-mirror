#!/usr/bin/env python3
"""
测试状态同步问题：网页端审批动作与企业微信审批状态不同步
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Quote
import sqlite3

def check_current_state():
    """检查当前报价单状态"""
    print("🔍 检查当前数据库状态...")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 查找最近的报价单
        cursor.execute('''
            SELECT id, quote_number, status, approval_status, wecom_approval_id
            FROM quotes
            WHERE quote_number LIKE 'CIS-KS%'
            ORDER BY created_at DESC
            LIMIT 3
        ''')
        quotes = cursor.fetchall()

        print(f"\n📋 最近的报价单:")
        for quote in quotes:
            print(f"   ID: {quote[0]}, 编号: {quote[1]}, 状态: {quote[2]}, 审批状态: {quote[3]}, 企业微信ID: {quote[4]}")

            # 查看这个报价单的审批记录
            cursor.execute('''
                SELECT action, status, wecom_sp_no, created_at, comments
                FROM approval_records
                WHERE quote_id = ?
                ORDER BY created_at DESC
                LIMIT 3
            ''', (quote[0],))
            records = cursor.fetchall()

            print(f"     审批记录:")
            for record in records:
                print(f"       动作: {record[0]}, 状态: {record[1]}, 企业微信编号: {record[2]}, 时间: {record[3]}")
                if record[4]:
                    print(f"       备注: {record[4]}")
            print()

        return quotes[0] if quotes else None

    except Exception as e:
        print(f"❌ 检查状态时发生错误: {str(e)}")
        return None
    finally:
        conn.close()

def simulate_web_approval_action(quote_id: int):
    """模拟在网页端进行审批动作"""
    print(f"\n🖥️ 模拟网页端审批动作 (报价单ID: {quote_id})...")

    # 获取数据库连接
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # 查询报价单
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            print(f"❌ 找不到报价单 ID: {quote_id}")
            return False

        print(f"报价单状态: {quote.status}, 审批状态: {quote.approval_status}")

        # 模拟审批操作（直接修改数据库，模拟API调用）
        conn = sqlite3.connect('app/test.db')
        cursor = conn.cursor()

        # 添加一条审批记录（模拟网页端操作）
        cursor.execute('''
            INSERT INTO approval_records
            (quote_id, action, status, comments, created_at, operation_channel)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            quote_id,
            "approve",  # 模拟批准操作
            "completed",
            "网页端模拟批准操作",
            datetime.utcnow(),
            "web"  # 标记为网页端操作
        ))

        # 更新报价单状态
        cursor.execute('''
            UPDATE quotes
            SET status = ?, approval_status = ?
            WHERE id = ?
        ''', ("approved", "approved", quote_id))

        conn.commit()
        conn.close()

        print(f"✅ 网页端审批操作完成")
        return True

    except Exception as e:
        print(f"❌ 模拟审批操作时发生错误: {str(e)}")
        return False
    finally:
        db.close()

def check_wecom_synchronization(quote_id: int):
    """检查企业微信同步状态"""
    print(f"\n🔄 检查企业微信同步状态 (报价单ID: {quote_id})...")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 查看报价单的企业微信审批ID
        cursor.execute('''
            SELECT wecom_approval_id, status, approval_status
            FROM quotes
            WHERE id = ?
        ''', (quote_id,))
        quote_info = cursor.fetchone()

        if quote_info:
            wecom_id, status, approval_status = quote_info
            print(f"报价单状态: {status}, 审批状态: {approval_status}")
            print(f"企业微信审批ID: {wecom_id}")

            # 查看所有审批记录
            cursor.execute('''
                SELECT action, status, wecom_sp_no, operation_channel, created_at, comments
                FROM approval_records
                WHERE quote_id = ?
                ORDER BY created_at ASC
            ''', (quote_id,))
            records = cursor.fetchall()

            print(f"\n📜 完整审批记录:")
            for i, record in enumerate(records, 1):
                channel = record[3] or "unknown"
                print(f"   {i}. 动作: {record[0]}, 状态: {record[1]}, 渠道: {channel}, 企业微信编号: {record[2]}")
                print(f"      时间: {record[4]}, 备注: {record[5]}")

            # 分析同步问题
            web_actions = [r for r in records if r[3] == 'web']
            wecom_actions = [r for r in records if r[3] in ['wecom', 'internal']]

            print(f"\n🔍 同步分析:")
            print(f"   网页端操作: {len(web_actions)} 条")
            print(f"   企业微信操作: {len(wecom_actions)} 条")

            if web_actions and not any(r[2] for r in web_actions):  # 网页端操作没有wecom_sp_no
                print(f"   ⚠️ 问题: 网页端操作没有同步到企业微信 (缺少wecom_sp_no)")
                return False

            return True
        else:
            print(f"❌ 找不到报价单 ID: {quote_id}")
            return False

    except Exception as e:
        print(f"❌ 检查同步状态时发生错误: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 测试状态同步问题")

    # 步骤1: 检查当前状态
    recent_quote = check_current_state()

    if recent_quote:
        quote_id = recent_quote[0]

        # 步骤2: 模拟网页端审批操作
        if simulate_web_approval_action(quote_id):

            # 步骤3: 检查同步状态
            check_wecom_synchronization(quote_id)

        print(f"\n💡 问题总结:")
        print(f"   1. 网页端审批操作不会自动同步到企业微信")
        print(f"   2. 需要在网页端操作后调用企业微信API更新状态")
        print(f"   3. operation_channel字段可以区分操作来源")
    else:
        print(f"❌ 没有找到可用的报价单进行测试")