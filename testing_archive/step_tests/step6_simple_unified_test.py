#!/usr/bin/env python3
"""
Step 6 简化统一审批系统测试
测试统一审批服务的基本功能，不依赖运行中的服务器
"""

import os
import sys
import json
from datetime import datetime

# 禁用代理设置
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

def test_imports():
    """测试关键模块导入"""
    print("🔧 测试模块导入...")
    try:
        # 测试数据库连接
        from app.database import get_db
        print("   ✅ 数据库模块导入成功")

        # 测试模型
        from app.models import Quote, User, ApprovalRecord
        print("   ✅ 数据模型导入成功")

        # 测试统一审批服务
        from app.services.unified_approval_service import UnifiedApprovalService
        print("   ✅ 统一审批服务导入成功")

        return True
    except Exception as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False

def test_database_data():
    """测试数据库中的数据"""
    print("\n🗄️ 测试数据库数据...")
    try:
        from app.database import SessionLocal
        from app.models import Quote

        db = SessionLocal()

        # 查询报价单数量
        quote_count = db.query(Quote).filter(Quote.is_deleted == False).count()
        print(f"   📊 数据库中报价单数量: {quote_count}")

        if quote_count > 0:
            # 获取第一个报价单
            first_quote = db.query(Quote).filter(Quote.is_deleted == False).first()
            print(f"   📄 第一个报价单ID: {first_quote.id}")
            print(f"   📄 报价单状态: {first_quote.status}")
            print(f"   📄 审批状态: {first_quote.approval_status}")
            print(f"   📄 审批方式: {getattr(first_quote, 'approval_method', '未设置')}")
            print(f"   📄 企微审批ID: {first_quote.wecom_approval_id or '无'}")

            return first_quote.id
        else:
            print("   ⚠️ 数据库中没有报价单")
            return None

    except Exception as e:
        print(f"   ❌ 数据库查询失败: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()

def test_unified_approval_service():
    """测试统一审批服务功能"""
    print("\n🔧 测试统一审批服务...")
    try:
        from app.database import SessionLocal
        from app.services.unified_approval_service import UnifiedApprovalService
        from app.models import Quote

        db = SessionLocal()

        # 获取一个报价单ID用于测试
        quote = db.query(Quote).filter(Quote.is_deleted == False).first()
        if not quote:
            print("   ⚠️ 没有可测试的报价单")
            return False

        quote_id = quote.id
        print(f"   🎯 使用报价单ID: {quote_id}")

        # 初始化统一审批服务
        service = UnifiedApprovalService(db)
        print("   ✅ 统一审批服务初始化成功")

        # 测试服务方法是否存在
        methods = ['submit_approval', 'approve', 'reject']
        for method in methods:
            if hasattr(service, method):
                print(f"   ✅ 方法 {method} 存在")
            else:
                print(f"   ❌ 方法 {method} 不存在")

        return True

    except Exception as e:
        print(f"   ❌ 统一审批服务测试失败: {e}")
        import traceback
        print(f"   详细错误: {traceback.format_exc()}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def test_api_file_structure():
    """测试API文件结构"""
    print("\n📁 测试API文件结构...")

    files_to_check = [
        'app/api/v1/endpoints/approval.py',
        'app/services/unified_approval_service.py',
        'app/api/v1/api.py'
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} 存在")
        else:
            print(f"   ❌ {file_path} 不存在")

    # 检查api.py中是否包含approval路由
    try:
        with open('app/api/v1/api.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'approval.router' in content:
                print("   ✅ approval路由已注册到主API")
            else:
                print("   ❌ approval路由未注册到主API")
    except Exception as e:
        print(f"   ❌ 检查API注册失败: {e}")

def generate_test_report():
    """生成测试报告"""
    print("\n" + "="*80)
    print("📊 Step 6 简化测试报告")
    print("="*80)

    # 运行所有测试
    results = {}

    print("🧪 开始测试...")
    results['imports'] = test_imports()
    results['database'] = test_database_data() is not None
    results['service'] = test_unified_approval_service()
    test_api_file_structure()

    # 统计结果
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    print(f"\n📈 测试结果: {passed}/{total} 通过")
    print(f"🎯 通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("🎉 所有基础测试通过！")
        system_status = "基础功能正常"
    elif passed >= total * 0.7:
        print("⚠️ 大部分测试通过，有少量问题")
        system_status = "部分功能异常"
    else:
        print("🚨 多项测试失败，需要修复")
        system_status = "系统存在重大问题"

    # 保存报告
    report = {
        "test_time": datetime.now().isoformat(),
        "test_type": "simplified_system_test",
        "results": results,
        "summary": {
            "total_tests": total,
            "passed_tests": passed,
            "pass_rate": passed/total*100,
            "system_status": system_status
        }
    }

    report_file = f"step6_simplified_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 测试报告已保存: {report_file}")

    return results

if __name__ == "__main__":
    print("🚀 Step 6: 统一审批系统简化测试")
    print("="*80)

    results = generate_test_report()

    print("\n✅ 简化测试完成")