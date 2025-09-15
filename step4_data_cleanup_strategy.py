#!/usr/bin/env python3
"""
Step 4: 数据清理策略和测试脚本
基于CLAUDE_WORKFLOW.md安全原则，只提供清理建议，不直接修改数据
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def create_cleanup_strategy():
    """创建安全的数据清理策略"""

    print("🧹 Step 4: 数据清理策略")
    print("=" * 50)

    # 基于分析结果的清理建议
    cleanup_recommendations = {
        "suspected_test_data": [
            {"customer": "ChinaTest", "reason": "客户名包含'Test'"},
            {"customer": "testonly", "reason": "客户名为'testonly'"},
            {"customer": "测试客户修复", "reason": "客户名包含'测试'"}
        ],
        "other_questionable_data": [
            {"customer": "666", "reason": "客户名为数字，可能是测试数据"},
            {"customer": "zzz", "reason": "客户名为'zzz'，可能是测试数据"},
            {"customer": "man", "reason": "客户名过于简单，可能是测试数据"}
        ]
    }

    print("📋 1. 清理建议分类:")
    print("-" * 30)

    print("🧪 高置信度测试数据 (建议清理):")
    for item in cleanup_recommendations["suspected_test_data"]:
        print(f"  • {item['customer']} - {item['reason']}")

    print("\n❓ 可疑数据 (需要确认):")
    for item in cleanup_recommendations["other_questionable_data"]:
        print(f"  • {item['customer']} - {item['reason']}")

    print(f"\n📝 2. 清理策略:")
    print("-" * 30)
    print("  1. 🔒 安全原则: 先软删除，观察一段时间，再硬删除")
    print("  2. 📊 保留统计: 清理前记录数据统计")
    print("  3. 🔄 可恢复: 所有清理操作都可以通过管理页面恢复")
    print("  4. 👥 权限控制: 只有超级管理员可以执行硬删除")

    print(f"\n🛠️ 3. 推荐清理步骤:")
    print("-" * 30)
    print("  1. 使用管理页面软删除明确的测试数据")
    print("  2. 保留可疑数据，等待业务确认")
    print("  3. 创建小规模的示例数据供测试使用")
    print("  4. 验证所有功能在清理后正常工作")

    return cleanup_recommendations

def create_test_verification_script():
    """创建测试验证脚本"""

    print(f"\n🧪 4. 功能验证计划:")
    print("-" * 30)

    verification_steps = [
        {
            "step": "前端页面访问测试",
            "description": "验证http://localhost:3000/admin/database-quote-management可访问",
            "expected": "页面正常加载，显示报价单列表"
        },
        {
            "step": "权限控制测试",
            "description": "验证只有admin/super_admin可以访问管理页面",
            "expected": "普通用户无法访问或看到管理功能"
        },
        {
            "step": "软删除功能测试",
            "description": "使用管理页面软删除一条测试数据",
            "expected": "数据标记为删除，但可恢复"
        },
        {
            "step": "企业微信认证测试",
            "description": "通过隧道访问https://wecom-dev.chipinfos.com.cn",
            "expected": "企业微信用户可正常登录和使用"
        },
        {
            "step": "API功能测试",
            "description": "测试所有管理员API端点正常工作",
            "expected": "API返回正确的数据和状态码"
        }
    ]

    for i, step in enumerate(verification_steps, 1):
        print(f"  {i}. {step['step']}")
        print(f"     📝 操作: {step['description']}")
        print(f"     ✅ 预期: {step['expected']}")
        print()

    return verification_steps

def generate_cleanup_report():
    """生成清理报告模板"""

    print(f"📊 5. 清理报告模板:")
    print("-" * 30)

    report_template = {
        "cleanup_date": datetime.now().isoformat(),
        "before_cleanup": {
            "total_quotes": 16,
            "normal_quotes": 15,
            "deleted_quotes": 1,
            "pending_approval": 11,
            "approved": 3,
            "draft": 1
        },
        "actions_taken": [
            # 这里记录实际执行的清理操作
        ],
        "after_cleanup": {
            # 清理后的统计将在这里更新
        },
        "verification_results": {
            # 验证测试的结果将在这里记录
        }
    }

    print("  📅 清理日期: 执行时自动记录")
    print("  📊 清理前统计: 已记录当前状态")
    print("  🔄 执行的操作: 清理时记录")
    print("  📈 清理后统计: 清理后更新")
    print("  ✅ 验证结果: 测试后记录")

    return report_template

if __name__ == "__main__":
    print("🔒 遵循CLAUDE_WORKFLOW.md安全原则")
    print("只提供清理建议，不直接修改数据\n")

    # 创建清理策略
    cleanup_recs = create_cleanup_strategy()

    # 创建验证计划
    verification_plan = create_test_verification_script()

    # 生成报告模板
    report_template = generate_cleanup_report()

    print(f"\n✅ 清理策略制定完成!")
    print("🔧 下一步: 使用前端管理页面执行安全的数据清理")
    print("🔗 管理页面: http://localhost:3000/admin/database-quote-management")