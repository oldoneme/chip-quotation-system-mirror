#!/usr/bin/env python3
"""调试前端快照PDF生成的辅助脚本"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.database import SessionLocal
from app.models import Quote, User
from app.services.quote_service import QuoteService


def _pick_user(db, quote: Quote, user_id: int | None) -> User:
    if user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise SystemExit(f"❌ 指定的用户ID {user_id} 不存在")
        return user

    if quote.creator:
        return quote.creator

    admin = (
        db.query(User)
        .filter(User.role.in_(["admin", "super_admin"]))
        .order_by(User.id.asc())
        .first()
    )
    if admin:
        return admin

    raise SystemExit("❌ 未找到可用于快照鉴权的用户，请指定 --user-id")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成报价单PDF快照并输出调试信息")
    parser.add_argument("quote_number", help="目标报价单号，例如 CIS-KS20250101XXX")
    parser.add_argument(
        "--user-id",
        type=int,
        help="用于快照鉴权的用户ID（默认使用报价创建者或管理员）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成PDF，忽略已有缓存",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        service = QuoteService(session)
        quote = service.get_quote_by_number(args.quote_number)
        if not quote:
            print(f"❌ 未找到报价单: {args.quote_number}")
            return 1

        quote_detail = service.load_quote_with_details(quote.id) or quote
        acting_user = _pick_user(session, quote_detail, args.user_id)

        cache = service.ensure_pdf_cache(quote_detail, acting_user, force=args.force)
        pdf_path = Path(cache.pdf_path)
        if not pdf_path.is_absolute():
            pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print("❌ PDF 文件生成失败，请检查日志")
            return 1

        output_path = Path.cwd() / "debug_quote.pdf"
        output_path.write_bytes(pdf_path.read_bytes())

        payload = {
            "event": "snapshot_debug",
            "quote_id": quote_detail.id,
            "quote_number": quote_detail.quote_number,
            "source": cache.source,
            "file_size": cache.file_size,
            "pdf_path": str(pdf_path),
            "output": str(output_path),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        if cache.source != "playwright":
            print("⚠️ 已使用 WeasyPrint 兜底，请检查前端快照是否可访问。")
        elif cache.file_size is not None and cache.file_size < 10_000:
            print("⚠️ 生成的PDF体积很小，可能捕获到登录页或空白页，请人工确认。")

        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
