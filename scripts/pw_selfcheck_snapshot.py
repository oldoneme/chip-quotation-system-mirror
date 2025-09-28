#!/usr/bin/env python3
"""Playwright snapshot自检脚本."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict

# 确保可以导入 backend 模块
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

DEFAULT_DB_PATH = (BACKEND_ROOT / 'app' / 'test.db').resolve()
os.environ.setdefault('DATABASE_URL', f'sqlite:///{DEFAULT_DB_PATH}')

from playwright.sync_api import sync_playwright

from app.database import SessionLocal
from app.models import User
from app.wecom_auth import AuthService
from app.auth import JWT_SECRET, JWT_ALG
import jwt

BASE = "https://wecom-dev.chipinfos.com.cn"


def _create_session_for_token(token: str) -> str:
    """根据快照JWT创建后台会话并返回session_token。"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.InvalidTokenError as exc:  # pragma: no cover - 运行时防御
        raise SystemExit(f"❌ 快照JWT无效: {exc}")

    userid = payload.get("sub")
    if not userid:
        raise SystemExit("❌ 快照JWT缺少sub字段，无法定位用户")

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.userid == userid).first()
        if not user:
            raise SystemExit(f"❌ 快照用户不存在: {userid}")
        auth_service = AuthService(session)
        user_session = auth_service.create_session(
            user,
            user_agent="playwright-selfcheck",
            ip_address="127.0.0.1",
        )
        return user_session.session_token
    finally:
        session.close()


def main(qno: str, token: str) -> None:
    detail = f"{BASE}/quote-detail/{qno}?userid=snapshot-bot&__snapshot_token={token}&jwt={token}"
    out_png = f"selfcheck_{qno}.png"
    out_pdf = f"selfcheck_{qno}.pdf"
    state: Dict[str, bool] = {"api_hit": False, "ready": False}

    session_token = _create_session_for_token(token)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--single-process",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            base_url=BASE,
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 900},
            extra_http_headers={
                "Authorization": f"Bearer {token}",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )

        def on_request_finished(request) -> None:
            if "/api/" in request.url:
                try:
                    response = request.response()
                    if response and response.status in (200, 304):
                        state["api_hit"] = True
                except Exception:
                    pass

        context.add_cookies(
            [
                {
                    "name": "admin_token",
                    "value": token,
                    "domain": "wecom-dev.chipinfos.com.cn",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False,
                    "sameSite": "Lax",
                },
                {
                    "name": "session_token",
                    "value": session_token,
                    "domain": "wecom-dev.chipinfos.com.cn",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False,
                    "sameSite": "Lax",
                },
                {
                    "name": "auth_token",
                    "value": token,
                    "domain": "wecom-dev.chipinfos.com.cn",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False,
                    "sameSite": "Lax",
                },
            ]
        )
        token_js = json.dumps(token)
        session_js = json.dumps(session_token)
        context.add_init_script(
            "(()=>{try{" \
            f"const t={token_js};" \
            f"const s={session_js};" \
            "sessionStorage.setItem('__snapshot_token',t);" \
            "sessionStorage.setItem('wework_authenticated','true');" \
            "localStorage.setItem('jwt',t);" \
            "localStorage.setItem('jwt_token',t);" \
            "localStorage.setItem('auth_token',t);" \
            "localStorage.setItem('session_token',s);" \
            "document.cookie=`session_token=${s}; path=/; secure`;" \
            "}catch(e){}})()"
        )

        page = context.new_page()
        page.on("requestfinished", on_request_finished)

        block_patterns = ("hot-update", "sockjs-node", "__webpack_hmr", ":3000/ws")
        page.route(
            "**/*",
            lambda route: route.abort()
            if any(pattern in route.request.url.lower() for pattern in block_patterns)
            else route.continue_(),
        )

        page.goto(detail, wait_until="commit", timeout=5_000)

        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                if page.evaluate("!!document.querySelector('#quote-ready')"):
                    state["ready"] = True
                    break
                if page.evaluate(
                    "!!document.querySelector('.ant-descriptions, .ant-card, .ant-table')"
                ):
                    state["ready"] = True
                    break
            except Exception:
                pass
            time.sleep(1.5)

        Path(out_png).parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=out_png, full_page=True)
        if state["ready"]:
            page.pdf(
                path=out_pdf,
                print_background=True,
                format="A4",
                prefer_css_page_size=True,
            )

        print(
            json.dumps(
                {
                    "quote_no": qno,
                    "api_hit": state["api_hit"],
                    "ready": state["ready"],
                    "png": out_png,
                    "pdf": out_pdf if state["ready"] else "",
                },
                ensure_ascii=False,
            )
        )

        context.close()
        browser.close()


if __name__ == "__main__":
    quote_no = sys.argv[1] if len(sys.argv) > 1 else ""
    token = os.environ.get("SNAP_TOKEN") or os.environ.get("T") or ""
    assert quote_no and token, (
        "Usage: SNAP_TOKEN=... python scripts/pw_selfcheck_snapshot.py <QUOTE_NO>"
    )
    main(quote_no, token)
