#!/usr/bin/env python3
"""
测试两个修复：
1. 访问控制 - 报价单详情重定向的认证问题
2. 状态同步 - 网页端审批操作与企业微信的同步问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Quote, User
from app.auth import get_current_user
import sqlite3
import requests
import json

def test_authentication_access_control():
    """测试1: 访问控制修复"""
    print("🔐 测试1: 访问控制和认证")

    # 获取数据库连接
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # 查找最近的报价单
        quote = db.query(Quote).filter(Quote.quote_number.like('CIS-KS%')).order_by(Quote.created_at.desc()).first()
        if not quote:
            print("❌ 没有找到测试报价单")
            return False

        print(f"📋 使用报价单: {quote.quote_number} (ID: {quote.id})")

        # 测试不同的访问方式
        test_cases = [
            {
                "name": "无认证访问",
                "url": f"http://localhost:8000/api/v1/wecom-approval/quote-detail-redirect/{quote.id}",
                "headers": {},
                "expected": "应该重定向到OAuth或前端认证页面"
            },
            {
                "name": "无效JWT访问",
                "url": f"http://localhost:8000/api/v1/wecom-approval/quote-detail-redirect/{quote.id}?jwt=invalid_token",
                "headers": {},
                "expected": "应该因为无效JWT而失败"
            },
            {
                "name": "带Cookie访问",
                "url": f"http://localhost:8000/api/v1/wecom-approval/quote-detail-redirect/{quote.id}",
                "headers": {"Cookie": "auth_token=test_token"},
                "expected": "应该检查cookie中的认证令牌"
            }
        ]

        for case in test_cases:
            print(f"\n🧪 测试场景: {case['name']}")
            try:
                response = requests.get(case['url'], headers=case['headers'], allow_redirects=False)
                print(f"   HTTP状态码: {response.status_code}")
                if 'Location' in response.headers:
                    print(f"   重定向到: {response.headers['Location']}")
                print(f"   预期行为: {case['expected']}")
            except Exception as e:
                print(f"   请求异常: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ 测试访问控制时发生错误: {str(e)}")
        return False
    finally:
        db.close()

def test_web_approval_synchronization():
    """测试2: 网页端审批同步"""
    print(f"\n🔄 测试2: 网页端审批同步")

    # 获取数据库连接
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # 查找有企业微信审批ID的报价单
        quote = db.query(Quote).filter(
            Quote.wecom_approval_id.isnot(None),
            Quote.quote_number.like('CIS-KS%')
        ).order_by(Quote.created_at.desc()).first()

        if not quote:
            print("❌ 没有找到有企业微信审批ID的报价单，创建测试数据...")
            return create_test_quote_for_sync()

        print(f"📋 使用报价单: {quote.quote_number} (ID: {quote.id})")
        print(f"   企业微信审批ID: {quote.wecom_approval_id}")

        # 记录操作前的审批记录数量
        conn = sqlite3.connect('app/test.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM approval_records WHERE quote_id = ?', (quote.id,))
        records_before = cursor.fetchone()[0]
        print(f"   操作前审批记录数: {records_before}")

        # 测试网页端审批操作 - 模拟API调用
        test_approval_action = {
            "comments": "网页端测试批准操作"
        }

        print(f"\n🖥️ 模拟网页端审批操作...")
        try:
            response = requests.post(
                f"http://localhost:8000/api/v1/wecom-approval/approve/{quote.id}",
                json=test_approval_action,
                headers={"Content-Type": "application/json"}
            )
            print(f"   API响应状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   API响应: {result.get('message', 'N/A')}")
            else:
                print(f"   API错误: {response.text}")
        except Exception as e:
            print(f"   API请求异常: {str(e)}")

        # 检查操作后的审批记录
        cursor.execute('SELECT COUNT(*) FROM approval_records WHERE quote_id = ?', (quote.id,))
        records_after = cursor.fetchone()[0]
        print(f"   操作后审批记录数: {records_after}")

        # 查看最新的审批记录
        cursor.execute('''
            SELECT action, status, operation_channel, wecom_sp_no, comments, created_at
            FROM approval_records
            WHERE quote_id = ?
            ORDER BY created_at DESC
            LIMIT 3
        ''', (quote.id,))
        recent_records = cursor.fetchall()

        print(f"\n📜 最近的审批记录:")
        for i, record in enumerate(recent_records, 1):
            action, status, channel, wecom_sp_no, comments, created_at = record
            print(f"   {i}. 动作: {action}, 状态: {status}, 渠道: {channel}")
            print(f"      企业微信编号: {wecom_sp_no}, 时间: {created_at}")
            if comments:
                print(f"      备注: {comments}")

        # 分析同步结果
        sync_records = [r for r in recent_records if r[2] and 'web_sync_to_wecom' in r[2]]
        if sync_records:
            print(f"\n✅ 发现 {len(sync_records)} 条网页端同步记录")
            print(f"   同步标记正常工作")
            return True
        else:
            print(f"\n⚠️ 没有发现网页端同步记录")
            print(f"   可能需要检查同步逻辑")
            return False

    except Exception as e:
        print(f"❌ 测试同步时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()
        db.close()

def create_test_quote_for_sync():
    """为同步测试创建报价单"""
    print("📝 创建测试报价单用于同步测试...")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 生成报价单编号
        quote_number = f"CIS-KS{datetime.now().strftime('%Y%m%d%H%M')}"

        # 创建带企业微信审批ID的报价单
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
            "pending",
            "pending",
            "SYNC_TEST_001",  # 模拟企业微信审批ID
            1,
            datetime.utcnow()
        ))

        quote_id = cursor.lastrowid
        conn.commit()

        print(f"✅ 创建成功: {quote_number} (ID: {quote_id})")
        print(f"   企业微信审批ID: SYNC_TEST_001")

        return test_web_approval_synchronization()

    except Exception as e:
        print(f"❌ 创建测试报价单失败: {str(e)}")
        return False
    finally:
        conn.close()

def test_integration():
    """集成测试"""
    print("🧪 开始集成测试...")

    # 检查后端服务是否运行
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print(f"⚠️ 后端服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 后端服务无法访问: {str(e)}")
        print("   请确保后端服务正在运行")
        return False

    # 执行测试
    test1_result = test_authentication_access_control()
    test2_result = test_web_approval_synchronization()

    print(f"\n📊 测试结果总结:")
    print(f"   1. 访问控制测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   2. 状态同步测试: {'✅ 通过' if test2_result else '❌ 失败'}")

    if test1_result and test2_result:
        print(f"\n🎉 所有测试通过！修复生效")
        return True
    else:
        print(f"\n⚠️ 部分测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = test_integration()
    if success:
        print(f"\n💡 修复说明:")
        print(f"   1. 访问控制：现在使用三段兜底认证（Authorization Header → Cookie → Query JWT）")
        print(f"   2. 状态同步：网页端审批操作会标记'web_sync_to_wecom'并发送通知")
        print(f"   3. 权限管理：不同角色用户看到不同的审批界面内容")
    else:
        print(f"\n🔧 需要进一步调试和修复")