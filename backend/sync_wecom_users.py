#!/usr/bin/env python3
"""
同步企业微信用户到数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.wecom_auth import WeComOAuth, AuthService

def sync_wecom_users():
    """同步企业微信用户和部门信息"""
    print("🔄 开始同步企业微信用户和部门...")
    
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        wecom = WeComOAuth()
        
        # 1. 同步部门信息
        print("📁 同步部门信息...")
        try:
            dept_count = wecom.sync_departments(db)
            print(f"✅ 同步了 {dept_count} 个部门")
        except Exception as e:
            print(f"⚠️  部门同步失败: {e}")
        
        # 2. 获取当前所有用户（如果有的话）
        from app.models import User
        existing_users = db.query(User).all()
        print(f"📊 数据库中现有用户数: {len(existing_users)}")
        
        if existing_users:
            print("👥 现有用户列表:")
            for user in existing_users:
                print(f"  - {user.name} ({user.userid}) - {user.role}")
        else:
            print("⚠️  数据库中没有用户，需要通过企业微信登录创建用户")
        
        print("\n" + "="*60)
        print("✅ 用户同步检查完成")
        print("\n📝 下一步:")
        print("1. 确保企业微信配置正确")
        print("2. 通过企业微信应用登录创建用户")
        print("3. 在管理后台设置用户权限")
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    sync_wecom_users()