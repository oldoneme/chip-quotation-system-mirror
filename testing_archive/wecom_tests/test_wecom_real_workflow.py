#!/usr/bin/env python3
"""
企业微信端实际工作流测试监控
监控企业微信端用户操作，验证统一审批系统的实际效果
"""

import sys
import time
import sqlite3
from datetime import datetime
sys.path.append('/home/qixin/projects/chip-quotation-system/backend')

def monitor_real_workflow():
    """监控实际工作流程"""
    print("🔍 企业微信端实际工作流测试监控启动...")
    print("📱 请在企业微信端进行以下操作测试:\n")

    print("🎯 测试步骤:")
    print("1️⃣ 在企业微信中打开芯片报价系统")
    print("2️⃣ 创建一个新的报价单")
    print("3️⃣ 填写报价单信息并提交审批")
    print("4️⃣ 观察系统行为和数据变化\n")

    # 数据库连接
    try:
        db_path = '/home/qixin/projects/chip-quotation-system/backend/app/test.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("✅ 数据库连接成功，开始监控...")

        # 获取初始状态
        cursor.execute("SELECT COUNT(*) FROM quotes")
        initial_quote_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM approval_records")
        initial_approval_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT quote_number, status, approval_status, created_at
            FROM quotes
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_quotes = cursor.fetchall()

        print(f"📊 当前数据库状态:")
        print(f"   • 报价单总数: {initial_quote_count}")
        print(f"   • 审批记录总数: {initial_approval_count}")
        print(f"   • 最近5个报价单:")

        for quote in recent_quotes:
            quote_number, status, approval_status, created_at = quote
            print(f"     - {quote_number}: status='{status}', approval_status='{approval_status}', 创建时间={created_at}")

        print(f"\n🔄 开始实时监控... (每5秒检查一次变化)")
        print(f"   按 Ctrl+C 停止监控\n")

        try:
            while True:
                time.sleep(5)

                # 检查报价单变化
                cursor.execute("SELECT COUNT(*) FROM quotes")
                current_quote_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM approval_records")
                current_approval_count = cursor.fetchone()[0]

                if current_quote_count > initial_quote_count:
                    # 有新报价单创建
                    cursor.execute("""
                        SELECT quote_number, status, approval_status, total_amount, customer_name, created_at
                        FROM quotes
                        ORDER BY created_at DESC
                        LIMIT 1
                    """)
                    new_quote = cursor.fetchone()
                    quote_number, status, approval_status, total_amount, customer_name, created_at = new_quote

                    print(f"🆕 检测到新报价单创建!")
                    print(f"   • 报价单号: {quote_number}")
                    print(f"   • 客户: {customer_name}")
                    print(f"   • 金额: {total_amount}")
                    print(f"   • 状态: status='{status}', approval_status='{approval_status}'")
                    print(f"   • 创建时间: {created_at}")

                    # 验证统一审批系统的影响
                    if status == 'draft' and approval_status == 'not_submitted':
                        print(f"   ✅ 新报价单状态正确: 草稿状态，未提交审批")
                    else:
                        print(f"   ⚠️ 状态异常: 期望draft+not_submitted")

                    initial_quote_count = current_quote_count

                if current_approval_count > initial_approval_count:
                    # 有新审批记录
                    cursor.execute("""
                        SELECT ar.quote_id, ar.action, ar.status, ar.comments, ar.created_at, q.quote_number
                        FROM approval_records ar
                        JOIN quotes q ON ar.quote_id = q.id
                        ORDER BY ar.created_at DESC
                        LIMIT 1
                    """)
                    new_approval = cursor.fetchone()

                    if new_approval:
                        quote_id, action, ar_status, comments, ar_created_at, quote_number = new_approval

                        print(f"📋 检测到新审批记录!")
                        print(f"   • 报价单: {quote_number}")
                        print(f"   • 审批动作: {action}")
                        print(f"   • 审批状态: {ar_status}")
                        print(f"   • 审批意见: {comments}")
                        print(f"   • 记录时间: {ar_created_at}")

                        # 检查是否使用了统一审批系统的标准格式
                        if "(通过" in comments and ("企业微信审批" in comments or "内部审批" in comments):
                            print(f"   ✅ 检测到统一审批系统的标准化格式!")
                            if "企业微信审批" in comments:
                                print(f"   🎯 使用了企业微信审批提供者")
                            else:
                                print(f"   🎯 使用了内部审批提供者")
                        else:
                            print(f"   ⚠️ 未检测到统一审批格式，可能使用了旧系统")

                        # 检查相关报价单的状态同步
                        cursor.execute("""
                            SELECT status, approval_status
                            FROM quotes
                            WHERE quote_number = ?
                        """, (quote_number,))
                        quote_status = cursor.fetchone()

                        if quote_status:
                            q_status, q_approval_status = quote_status
                            print(f"   📊 报价单状态同步检查: status='{q_status}', approval_status='{q_approval_status}'")

                            # 验证状态同步逻辑
                            if action == 'submit' and q_status == 'pending' and q_approval_status == 'pending':
                                print(f"   ✅ 提交审批后状态同步正确")
                            elif action == 'approve' and q_status == 'approved' and q_approval_status == 'approved':
                                print(f"   ✅ 批准后状态同步正确")
                            elif action == 'reject' and q_status == 'rejected' and q_approval_status == 'rejected':
                                print(f"   ✅ 拒绝后状态同步正确")

                    initial_approval_count = current_approval_count

                # 简单的心跳显示
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - 监控中... (报价单:{current_quote_count}, 审批记录:{current_approval_count})")

        except KeyboardInterrupt:
            print(f"\n🛑 监控已停止")

            # 最终统计
            cursor.execute("SELECT COUNT(*) FROM quotes")
            final_quote_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM approval_records")
            final_approval_count = cursor.fetchone()[0]

            print(f"\n📊 监控期间变化:")
            print(f"   • 新增报价单: {final_quote_count - initial_quote_count}")
            print(f"   • 新增审批记录: {final_approval_count - initial_approval_count}")

            if final_quote_count > initial_quote_count or final_approval_count > initial_approval_count:
                print(f"\n🎉 检测到用户操作！Step 2统一审批系统正在工作")
            else:
                print(f"\n📝 未检测到新操作，建议在企业微信端执行测试步骤")

        conn.close()

    except Exception as e:
        print(f"❌ 数据库监控失败: {e}")
        print(f"   请确认数据库路径正确")

def generate_test_report():
    """生成测试报告"""
    print(f"\n📋 企业微信端实际测试验证项目:")
    print(f"\n🔍 通过用户操作可以验证的功能:")

    test_items = [
        {
            "项目": "统一审批系统集成",
            "验证方法": "创建报价单→提交审批",
            "期望结果": "QuoteService使用统一审批服务，审批记录包含方法标识",
            "检测点": "approval_records.comments包含'(通过XX审批)'"
        },
        {
            "项目": "智能审批路由选择",
            "验证方法": "提交审批操作",
            "期望结果": "系统选择内部审批提供者（企业微信无配置时）",
            "检测点": "审批记录显示'内部审批'"
        },
        {
            "项目": "状态字段同步",
            "验证方法": "审批状态变更操作",
            "期望结果": "status和approval_status保持一致",
            "检测点": "两个状态字段映射正确"
        },
        {
            "项目": "审批记录标准化",
            "验证方法": "任何审批操作",
            "期望结果": "记录格式统一，包含审批方法标识",
            "检测点": "comments字段格式标准化"
        },
        {
            "项目": "回退机制验证",
            "验证方法": "正常审批流程",
            "期望结果": "无企业微信配置时系统仍正常工作",
            "检测点": "功能完全可用"
        }
    ]

    for i, item in enumerate(test_items, 1):
        print(f"\n{i}️⃣ **{item['项目']}**")
        print(f"   📝 验证方法: {item['验证方法']}")
        print(f"   🎯 期望结果: {item['期望结果']}")
        print(f"   🔍 检测点: {item['检测点']}")

    print(f"\n💡 测试建议:")
    print(f"   1. 先运行此监控脚本")
    print(f"   2. 在企业微信端进行实际操作")
    print(f"   3. 观察监控输出，验证Step 2功能")
    print(f"   4. 检查数据库记录格式和状态同步")

if __name__ == "__main__":
    generate_test_report()
    print(f"\n" + "="*60)
    monitor_real_workflow()