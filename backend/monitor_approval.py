#!/usr/bin/env python3
"""
企业微信审批状态监控脚本
实时监控CIS-KS20250830002的审批状态变化
"""

import sys
import time
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Quote

def monitor_approval_status():
    """监控审批状态变化"""
    print("🔍 开始监控 CIS-KS20250830002 审批状态")
    print("=" * 60)
    print("📋 审批单号: 202509010097")
    print("🔄 按 Ctrl+C 停止监控\n")
    
    last_status = None
    last_approval_status = None
    
    try:
        while True:
            db = next(get_db())
            try:
                # 获取报价单状态
                quote = db.query(Quote).filter(Quote.quote_number == 'CIS-KS20250830002').first()
                
                if quote:
                    current_status = quote.status
                    current_approval_status = quote.approval_status
                    
                    # 检查状态是否有变化
                    if (current_status != last_status or 
                        current_approval_status != last_approval_status):
                        
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        print(f"🕒 [{timestamp}] 状态更新:")
                        print(f"   报价单状态: {current_status}")
                        print(f"   审批状态: {current_approval_status}")
                        
                        if quote.approved_at:
                            print(f"   批准时间: {quote.approved_at}")
                        if quote.approved_by:
                            print(f"   批准人: {quote.approved_by}")
                        if quote.rejection_reason:
                            print(f"   拒绝原因: {quote.rejection_reason}")
                        
                        print("-" * 40)
                        
                        last_status = current_status
                        last_approval_status = current_approval_status
                        
                        # 如果审批完成，显示最终结果
                        if current_status in ['approved', 'rejected']:
                            print("🎉 审批流程完成!")
                            print(f"最终状态: {current_status}")
                            if current_status == 'approved':
                                print("✅ 审批通过")
                            else:
                                print("❌ 审批被拒绝")
                            break
                    
                else:
                    print("❌ 未找到报价单 CIS-KS20250830002")
                    break
                    
            finally:
                db.close()
            
            # 等待5秒后再次检查
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 监控已停止")
        print("💡 如需再次监控，请重新运行此脚本")

if __name__ == "__main__":
    monitor_approval_status()