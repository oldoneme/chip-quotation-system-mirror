#!/usr/bin/env python3
"""
调试报价单API问题
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Quote
from app.services.quote_service import QuoteService
from app.schemas import QuoteFilter

def test_service_directly():
    """直接测试服务层"""
    print("🔧 直接测试服务层...")
    
    db = SessionLocal()
    try:
        # 直接查询数据库
        quotes = db.query(Quote).all()
        print(f"✅ 数据库中共有 {len(quotes)} 条报价单记录")
        
        for quote in quotes[:3]:
            print(f"   - {quote.quote_number}: {quote.title} ({quote.status})")
        
        # 测试服务
        service = QuoteService(db)
        filter_params = QuoteFilter(page=1, size=5)
        
        print("\n🔍 测试服务层获取列表...")
        try:
            quotes, total = service.get_quotes(filter_params)
            print(f"✅ 服务层测试成功: 获取到 {len(quotes)} 条记录，总计 {total} 条")
            return True
        except Exception as e:
            print(f"❌ 服务层测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_service_directly()