#!/usr/bin/env python3
"""
测试新的报价单号生成系统
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal
from app.services.quote_service import QuoteService
from app.schemas import QuoteCreate, QuoteItemCreate
from datetime import datetime

def test_quote_numbering():
    """测试报价单号生成"""
    db = SessionLocal()
    quote_service = QuoteService(db)
    
    print("🧪 测试报价单号生成系统")
    print("=" * 50)
    
    # 测试不同报价单位的缩写
    test_units = ["昆山芯信安", "苏州芯昱安", "上海芯睿安", "珠海芯创安"]
    expected_abbr = ["KS", "SZ", "SH", "ZH"]
    
    print("1. 测试报价单位缩写映射:")
    for unit, expected in zip(test_units, expected_abbr):
        abbr = quote_service.get_quote_unit_abbreviation(unit)
        status = "✅" if abbr == expected else "❌"
        print(f"   {status} {unit} -> {abbr} (期望: {expected})")
    
    print("\n2. 测试报价单号生成:")
    
    # 测试每个单位的报价单号生成
    for unit in test_units:
        quote_number = quote_service.generate_quote_number(unit)
        abbr = quote_service.get_quote_unit_abbreviation(unit)
        today = datetime.now().strftime("%Y%m%d")
        expected_prefix = f"CIS-{abbr}{today}"
        
        if quote_number.startswith(expected_prefix):
            print(f"   ✅ {unit}: {quote_number}")
        else:
            print(f"   ❌ {unit}: {quote_number} (期望前缀: {expected_prefix})")
    
    print("\n3. 测试同一单位多个报价单的序号递增:")
    
    # 测试昆山芯信安的连续报价单号
    unit = "昆山芯信安"
    quote_numbers = []
    
    for i in range(3):
        quote_number = quote_service.generate_quote_number(unit)
        quote_numbers.append(quote_number)
        
        # 创建一个测试报价单来占用这个号码
        try:
            test_quote_data = QuoteCreate(
                title=f"测试报价单 {i+1}",
                quote_type="engineering",
                customer_name="测试客户",
                quote_unit=unit,
                items=[]
            )
            
            # 使用用户ID 1 (假设存在)
            quote = quote_service.create_quote(test_quote_data, 1)
            print(f"   ✅ 创建测试报价单: {quote.quote_number}")
            
        except Exception as e:
            print(f"   ⚠️  无法创建测试报价单 (可能缺少用户): {e}")
            break
    
    print(f"\n4. 生成的报价单号序列: {quote_numbers}")
    
    # 检查序号是否递增
    if len(quote_numbers) >= 2:
        for i in range(1, len(quote_numbers)):
            prev_seq = int(quote_numbers[i-1][-3:])
            curr_seq = int(quote_numbers[i][-3:])
            if curr_seq == prev_seq + 1:
                print(f"   ✅ 序号递增正确: {prev_seq} -> {curr_seq}")
            else:
                print(f"   ❌ 序号递增错误: {prev_seq} -> {curr_seq}")
    
    db.close()
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    test_quote_numbering()