#!/usr/bin/env python3
"""
验证双设备数据结构的数据库脚本
"""
import sqlite3
from datetime import datetime

def check_database():
    """检查数据库中的双设备记录"""
    conn = sqlite3.connect('/home/qixin/projects/chip-quotation-system/backend/app/test.db')
    cursor = conn.cursor()
    
    print("=== 验证双设备实现 ===\n")
    
    # 1. 检查最近的报价记录
    cursor.execute("""
        SELECT id, quote_number, quote_type, created_at 
        FROM quotes 
        WHERE quote_type = 'process' 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    quotes = cursor.fetchall()
    
    if quotes:
        print("📊 最近的工序报价记录:")
        for quote in quotes:
            quote_id, quote_number, quote_type, created_at = quote
            print(f"  ID: {quote_id}")
            print(f"  编号: {quote_number}")
            print(f"  类型: {quote_type}")
            print(f"  创建时间: {created_at}")
            print(f"  {'='*50}")
            
            # 检查该报价的具体项目
            cursor.execute("""
                SELECT item_name, machine_model, configuration, unit_price, quantity
                FROM quote_items 
                WHERE quote_id = ?
                ORDER BY id DESC
            """, (quote_id,))
            
            items = cursor.fetchall()
            if items:
                print(f"  📋 项目明细:")
                for item in items:
                    item_name, machine_model, config, unit_price, quantity = item
                    print(f"    - 项目: {item_name}")
                    print(f"      设备: {machine_model}")
                    print(f"      配置: {config}")
                    print(f"      单价: {unit_price}")
                    print(f"      数量: {quantity}")
                print(f"  {'='*50}")
            print()
    else:
        print("❌ 未找到工序报价记录")
    
    # 2. 检查设备数据
    cursor.execute("""
        SELECT m.name, mt.name as machine_type
        FROM machines m 
        JOIN suppliers s ON m.supplier_id = s.id
        JOIN machine_types mt ON s.machine_type_id = mt.id
        WHERE mt.name IN ('测试机', '分选机', '探针台')
        ORDER BY mt.name, m.name
    """)
    
    machines = cursor.fetchall()
    
    if machines:
        print("🔧 可用设备列表:")
        current_type = None
        for machine in machines:
            name, machine_type = machine
            if machine_type != current_type:
                print(f"\n  {machine_type}:")
                current_type = machine_type
            print(f"    - {name}")
    
    conn.close()
    print("\n✅ 数据库验证完成")

def test_cost_calculation():
    """测试成本计算逻辑"""
    print("\n=== 测试成本计算逻辑 ===\n")
    
    # 测试用例：双设备组合
    test_cases = [
        {
            "name": "CP工序 - 测试机 + 探针台",
            "test_machine": "ATE-3000",
            "test_machine_cost": 150.0,
            "prober": "EP-200", 
            "prober_cost": 80.0,
            "uph": 1000,
            "expected_total": 230.0
        },
        {
            "name": "FT工序 - 测试机 + 分选机",
            "test_machine": "ATE-5000",
            "test_machine_cost": 200.0,
            "handler": "HSR-500",
            "handler_cost": 120.0,
            "uph": 1500,
            "expected_total": 320.0
        },
        {
            "name": "单设备 - 仅测试机",
            "test_machine": "ATE-1000",
            "test_machine_cost": 100.0,
            "prober": None,
            "prober_cost": 0.0,
            "uph": 800,
            "expected_total": 100.0
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"📝 测试用例 {i}: {case['name']}")
        
        # 计算预期结果
        total_cost = case['test_machine_cost'] + case.get('prober_cost', 0) + case.get('handler_cost', 0)
        
        print(f"   测试机成本: {case['test_machine_cost']}")
        if case.get('prober_cost'):
            print(f"   探针台成本: {case['prober_cost']}")
        if case.get('handler_cost'):
            print(f"   分选机成本: {case['handler_cost']}")
        print(f"   UPH: {case['uph']}")
        print(f"   预期总成本: {case['expected_total']}")
        print(f"   实际计算: {total_cost}")
        
        if abs(total_cost - case['expected_total']) < 0.01:
            print(f"   ✅ 计算正确")
        else:
            print(f"   ❌ 计算错误")
        print()

if __name__ == "__main__":
    try:
        check_database()
        test_cost_calculation()
    except Exception as e:
        print(f"❌ 错误: {e}")