#!/usr/bin/env python3
"""
测试报价单号生成修复
验证排除软删除记录后编号生成是否正常
"""

import sys
import os
from datetime import datetime

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.services.quote_service import QuoteService

def test_quote_number_generation():
    """测试报价单号生成修复"""
    print("🧪 测试报价单号生成修复")
    print(f"⏰ 测试时间: {datetime.now()}")
    print("=" * 50)

    db = SessionLocal()
    try:
        service = QuoteService(db)

        print("1️⃣ 测试报价单号生成...")
        quote_number = service.generate_quote_number("昆山芯信安")
        print(f"   生成的报价单号: {quote_number}")

        # 应该生成 CIS-KS20250916001 因为没有未删除的同日记录
        expected = "CIS-KS20250916001"
        if quote_number == expected:
            print(f"   ✅ 生成正确: {quote_number}")
            print("   🎉 编号生成逻辑修复成功!")
            return True
        else:
            print(f"   ⚠️  预期: {expected}, 实际: {quote_number}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    success = test_quote_number_generation()

    print("\n" + "="*50)
    if success:
        print("🎉 报价单号生成逻辑修复成功!")
        print("   现在可以正常创建新报价单了。")
    else:
        print("💥 修复验证失败!")
        print("   需要进一步检查生成逻辑。")