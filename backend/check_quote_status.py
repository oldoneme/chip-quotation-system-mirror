#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Quote, User, ApprovalTimeline

def check_quote_status():
    """检查最新报价单状态"""
    print("🔧 检查最新报价单状态")
    print("=" * 50)

    db = next(get_db())

    try:
        # 查询CIS-KS20250918001报价单
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250918001").first()
        if not quote:
            print("❌ 找不到报价单 CIS-KS20250918001")
            # 查询最新的报价单
            latest_quote = db.query(Quote).order_by(Quote.id.desc()).first()
            if latest_quote:
                print(f"📋 最新报价单: {latest_quote.quote_number}")
                quote = latest_quote
            else:
                print("❌ 没有任何报价单")
                return

        print(f"📋 报价单: {quote.quote_number}")
        print(f"📊 状态: {quote.status}")
        print(f"📊 审批状态: {quote.approval_status}")
        print(f"📊 创建者ID: {quote.created_by}")

        # 查询审批历史记录
        print(f"\n📝 审批历史记录:")
        timelines = db.query(ApprovalTimeline).filter(ApprovalTimeline.third_no == str(quote.id)).order_by(ApprovalTimeline.created_at.desc()).all()
        for timeline in timelines:
            status_text = {1: "审批中", 2: "已同意", 3: "已拒绝", 4: "已取消"}.get(timeline.status, f"未知({timeline.status})")
            print(f"   {timeline.created_at}: {status_text} (Event ID: {timeline.event_id})")
            if timeline.sp_no:
                print(f"      SpNo: {timeline.sp_no}")

    except Exception as e:
        print(f"❌ 检查异常: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    check_quote_status()