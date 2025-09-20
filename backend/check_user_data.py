#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Quote, User

def check_user_data():
    """检查用户数据"""
    print("🔧 检查用户数据")
    print("=" * 50)

    db = next(get_db())

    try:
        # 查询报价单的创建者
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250918001").first()
        if not quote:
            print("❌ 找不到报价单")
            return

        print(f"📋 报价单 {quote.quote_number}")
        print(f"📊 创建者ID: {quote.created_by}")

        # 查询创建者信息
        creator = db.query(User).filter(User.id == quote.created_by).first()
        if creator:
            print(f"👤 创建者信息:")
            print(f"   ID: {creator.id}")
            print(f"   姓名: {creator.name}")
            print(f"   企业微信userid: {creator.userid}")
            print(f"   角色: {creator.role}")
            print(f"   部门: {creator.department}")
            print(f"   职位: {creator.position}")
        else:
            print("❌ 找不到创建者")

        # 查询所有用户，看看有哪些有效的企业微信userid
        print(f"\n👥 所有用户的企业微信userid:")
        users = db.query(User).all()
        for user in users:
            print(f"   用户 {user.id} ({user.name}): userid='{user.userid}'")

    except Exception as e:
        print(f"❌ 检查异常: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    check_user_data()