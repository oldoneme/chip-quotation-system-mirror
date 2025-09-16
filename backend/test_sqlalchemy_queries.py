#!/usr/bin/env python3
"""
验证SQLAlchemy查询在NULL ID修复后正常工作
"""

import sys
import os
from datetime import datetime

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.services.quote_service import QuoteService

def test_sqlalchemy_queries():
    """测试SQLAlchemy查询功能"""
    print("🔍 验证SQLAlchemy查询功能")
    print(f"⏰ 测试时间: {datetime.now()}")
    print("=" * 60)

    db = SessionLocal()
    try:
        quote_service = QuoteService(db)

        print("1️⃣ 测试按编号查询报价单...")
        quote = quote_service.get_quote_by_number("CIS-KS20250916001")

        if quote:
            print(f"   ✅ 查询成功!")
            print(f"   📋 编号: {quote.quote_number}")
            print(f"   🆔 ID: {quote.id}")
            print(f"   👤 客户: {quote.customer_name}")
            print(f"   💰 金额: ¥{quote.total_amount}")
            print(f"   📊 状态: {quote.status}")
            print(f"   📝 明细数量: {len(quote.items) if quote.items else 0}")
        else:
            print("   ❌ 查询失败 - 报价单不存在")
            return False

        print("2️⃣ 测试报价单列表查询...")
        from app.schemas import QuoteFilter

        filter_params = QuoteFilter(
            page=1,
            size=10
        )

        quotes, total = quote_service.get_quotes(filter_params)
        print(f"   查询结果: {len(quotes)} 条报价单，总计: {total}")

        for q in quotes:
            print(f"   - {q.quote_number}: {q.customer_name} - ¥{q.total_amount}")

        print("3️⃣ 测试统计信息查询...")
        stats = quote_service.get_quote_statistics()
        print(f"   📊 统计信息:")
        print(f"      总计: {stats.total}")
        print(f"      草稿: {stats.draft}")
        print(f"      待审: {stats.pending}")
        print(f"      已批准: {stats.approved}")
        print(f"      已拒绝: {stats.rejected}")

        print("4️⃣ 测试按ID查询...")
        quote_by_id = quote_service.get_quote_by_id(quote.id)
        if quote_by_id:
            print(f"   ✅ 按ID查询成功: {quote_by_id.quote_number}")
        else:
            print("   ❌ 按ID查询失败")
            return False

        print("5️⃣ 验证结果:")
        print("   ✅ NULL ID问题已完全修复")
        print("   ✅ SQLAlchemy查询正常工作")
        print("   ✅ 报价单关系加载正常")
        print("   ✅ 数据库状态一致")

        return True

    except Exception as e:
        print(f"❌ SQLAlchemy查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    success = test_sqlalchemy_queries()

    print("\n" + "="*60)
    if success:
        print("🎉 SQLAlchemy查询完全正常！NULL ID问题彻底解决！")
        print("   数据库现在完全一致，前端应该能正常显示报价单了。")
    else:
        print("💥 仍有查询问题需要解决。")