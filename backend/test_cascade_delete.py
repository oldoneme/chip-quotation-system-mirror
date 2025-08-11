#!/usr/bin/env python3
"""
测试级联删除功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import crud, models

def test_cascade_delete():
    db = SessionLocal()
    
    try:
        print("=== 级联删除测试 ===\n")
        
        # 测试1: 删除机器（应该删除其板卡配置）
        print("测试1: 测试删除机器的级联删除功能")
        
        # 查找一个有板卡的机器进行测试
        machine = db.query(models.Machine).filter(models.Machine.name == "JS3000").first()
        if not machine:
            print("未找到JS3000机器，跳过测试")
            return
            
        machine_id = machine.id
        print(f"选择机器: {machine.name} (ID: {machine_id})")
        
        # 查看该机器的板卡数量
        card_count_before = db.query(models.CardConfig).filter(models.CardConfig.machine_id == machine_id).count()
        print(f"删除前，该机器有 {card_count_before} 个板卡配置")
        
        if card_count_before == 0:
            print("该机器没有板卡配置，跳过测试")
            return
        
        # 执行级联删除
        print("执行删除...")
        result = crud.delete_machine(db, machine_id)
        
        if result:
            # 验证删除结果
            card_count_after = db.query(models.CardConfig).filter(models.CardConfig.machine_id == machine_id).count()
            machine_exists = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
            
            print(f"删除后，该机器的板卡配置数量: {card_count_after}")
            print(f"机器是否还存在: {'是' if machine_exists else '否'}")
            
            if card_count_after == 0 and not machine_exists:
                print("✅ 级联删除测试通过！")
            else:
                print("❌ 级联删除测试失败！")
        else:
            print("❌ 删除操作失败")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("注意: 这是一个破坏性测试，会真实删除数据！")
    response = input("确认继续吗? (y/N): ")
    if response.lower() == 'y':
        test_cascade_delete()
    else:
        print("测试已取消")