from __future__ import annotations

import json
import logging
import time
from datetime import datetime
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from playwright.sync_api import sync_playwright

from ..auth import create_user_token
from ..config import settings
from ..models import Quote, QuotePDFCache, User
from ..schemas import Quote as QuoteSchema
from ..wecom_auth import AuthService
from .weasyprint_pdf_service import weasyprint_pdf_service

SNAP_BASE = "https://wecom-dev.chipinfos.com.cn"
LOGGER = logging.getLogger("app.snapshot.frontend")


def generate_quote_pdf(
    quote_no: str,
    token: str,
    session_token: str,
    out_pdf: str,
    out_png: str,
    timeout_ms: int = 30_000,
) -> dict[str, str]:
    """用 Playwright 走前端路由生成报价单 PDF（优先前端样式，不回落 WeasyPrint）。"""
    out_pdf = str(out_pdf)
    out_png = str(out_png)
    detail_url = f"{SNAP_BASE}/quote-detail/{quote_no}?userid=snapshot-bot"

    token_js = json.dumps(token)
    block_patterns = ("hot-update", "sockjs-node", "__webpack_hmr", ":3000/ws")

    def _should_block(url: str) -> bool:
        url = url.lower()
        return any(pattern in url for pattern in block_patterns)

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
            base_url=SNAP_BASE,
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "Authorization": f"Bearer {token}",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "X-Snapshot-Client": "playwright-service",
            },
        )
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
        session_js = json.dumps(session_token)
        context.add_init_script(
            "(()=>{try{"
            f"const t={token_js};"
            f"const s={session_js};"
            "sessionStorage.setItem('__snapshot_token',t);"
            "sessionStorage.setItem('wework_authenticated','true');"
            "localStorage.setItem('jwt',t);"
            "localStorage.setItem('jwt_token',t);"
            "localStorage.setItem('auth_token',t);"
            "localStorage.setItem('session_token',s);"
            "document.cookie=`session_token=${s}; path=/; secure`;"
            "}catch(e){}})()"
        )

        page = context.new_page()
        page.route(
            "**/*",
            lambda route: route.abort()
            if _should_block(route.request.url)
            else route.continue_(),
        )

        page.goto(detail_url, wait_until="commit", timeout=8_000)
        page.wait_for_load_state("networkidle", timeout=15_000)

        def is_ready() -> bool:
            try:
                return (
                    page.evaluate("!!document.querySelector('#quote-ready')")
                    or page.evaluate(
                        "!!document.querySelector('.ant-descriptions, .ant-card, .ant-table')"
                    )
                )
            except Exception:
                return False

        deadline = time.time() + 8
        ready = False
        while time.time() < deadline:
            if is_ready():
                ready = True
                break
            time.sleep(0.5)

        if not ready:
            url_with_token = f"{detail_url}&__snapshot_token={token}&jwt={token}"
            page.goto(url_with_token, wait_until="domcontentloaded", timeout=15_000)
            try:
                page.wait_for_load_state("networkidle", timeout=8_000)
                page.reload(wait_until="domcontentloaded", timeout=6_000)
                page.wait_for_load_state("networkidle", timeout=8_000)
            except Exception:
                pass
            page.wait_for_selector(
                "#quote-ready, .ant-descriptions, .ant-card, .ant-table",
                timeout=timeout_ms,
            )

        Path(out_png).parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=out_png, full_page=True)
        page.pdf(
            path=out_pdf,
            print_background=True,
            format="A4",
            prefer_css_page_size=True,
        )

        context.close()
        browser.close()
        return {"quote_no": quote_no, "png": out_png, "pdf": out_pdf}


class FrontendSnapshotPDFService:
    """封装前端快照 PDF 生成逻辑，优先使用 Playwright，失败时回退 WeasyPrint。"""

    def __init__(self) -> None:
        self.media_root = Path("media/quotes")
        self.ready_selector = settings.SNAPSHOT_READY_SELECTOR or "#quote-ready"
        self.snapshot_timeout_ms = 30_000

    # ---------- 对外接口 ----------

    def generate_with_fallback(
        self,
        quote: Quote,
        user: User,
        db_session: Session,
        column_configs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        token = create_user_token(user, expires_seconds=1800, scope="snapshot")
        pdf_path, png_path = self._compute_output_paths(quote)

        content_hash = self._compute_quote_hash(quote, column_configs)

        try:
            auth_service = AuthService(db_session)
            user_session = auth_service.create_session(
                user, user_agent="playwright-snapshot", ip_address="127.0.0.1"
            )
            session_token = user_session.session_token
            result = generate_quote_pdf(
                quote_no=quote.quote_number,
                token=token,
                session_token=session_token,
                out_pdf=str(pdf_path),
                out_png=str(png_path),
                timeout_ms=self.snapshot_timeout_ms,
            )
            pdf_file = Path(result["pdf"])
            file_size = pdf_file.stat().st_size if pdf_file.exists() else 0
            payload = {
                "quote_id": quote.id,
                "quote_number": quote.quote_number,
                "source": "playwright",
                "pdf_path": str(pdf_file),
                "png_path": result.get("png"),
                "file_size": file_size,
                "content_hash": content_hash,
            }
            LOGGER.info(
                json.dumps(
                    {
                        "event": "snapshot_playwright_success",
                        **payload,
                    },
                    ensure_ascii=False,
                )
            )
            return payload
        except Exception as exc:
            LOGGER.error(
                json.dumps(
                    {
                        "event": "snapshot_playwright_failed",
                        "quote_id": quote.id,
                        "quote_number": quote.quote_number,
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
            pdf_bytes = weasyprint_pdf_service.generate_quote_pdf(
                self._serialize_quote(quote, column_configs)
            )
            pdf_path.write_bytes(pdf_bytes)
            fallback_payload = {
                "quote_id": quote.id,
                "quote_number": quote.quote_number,
                "source": "weasyprint",
                "pdf_path": str(pdf_path),
                "png_path": str(png_path),
                "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                "content_hash": content_hash,
            }
            LOGGER.warning(
                json.dumps(
                    {
                        "event": "snapshot_fallback_weasyprint",
                        **fallback_payload,
                    },
                    ensure_ascii=False,
                )
            )
            return fallback_payload

    def get_cached_pdf_path(self, quote: Quote) -> Optional[Path]:
        cache = getattr(quote, "pdf_cache", None)
        if not cache:
            return None
        path = Path(cache.pdf_path)
        if not path.is_absolute():
            path = Path(cache.pdf_path)
        return path if path.exists() else None

    def build_public_url_from_cache(self, cache: QuotePDFCache) -> str:
        path = Path(cache.pdf_path)
        if path.is_absolute():
            try:
                relative = path.relative_to(Path("media"))
            except ValueError:
                relative = path
        else:
            relative = path

        if relative.parts and relative.parts[0] == "media":
            relative = Path(*relative.parts[1:])

        return f"/media/{relative.as_posix()}"

    # ---------- 内部工具 ----------

    def _compute_output_paths(self, quote: Quote) -> tuple[Path, Path]:
        quote_dir = self.media_root / str(quote.id)
        quote_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = quote_dir / f"quote_{quote.quote_number}.pdf"
        png_path = quote_dir / f"quote_{quote.quote_number}.png"
        return pdf_path, png_path

    def _serialize_quote(
        self,
        quote: Quote,
        column_configs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        schema = QuoteSchema.model_validate(quote, from_attributes=True)
        data = schema.model_dump(mode="json")
        if column_configs:
            data["column_configs"] = column_configs
        return data

    def _compute_quote_hash(
        self,
        quote: Quote,
        column_configs: Optional[Dict[str, Any]] = None,
    ) -> str:
        serialized = self._sanitize_for_hash(self._serialize_quote(quote, column_configs))
        serialized_json = json.dumps(serialized, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized_json.encode("utf-8")).hexdigest()

    def compute_quote_hash(
        self,
        quote: Quote,
        column_configs: Optional[Dict[str, Any]] = None,
    ) -> str:
        return self._compute_quote_hash(quote, column_configs)

    def _sanitize_for_hash(self, data: Dict[str, Any]) -> Dict[str, Any]:
        meta_keys = {
            'status',
            'approval_status',
            'approval_method',
            'rejection_reason',
            'submitted_at',
            'approved_at',
            'approved_by',
            'wecom_approval_id',
            'current_approver_id',
            'deleted_at',
            'deleted_by',
            'is_deleted',
            'created_at',
            'updated_at',
            'pdf_cache',
        }

        sanitized: Dict[str, Any] = {}
        for key, value in data.items():
            if key in meta_keys:
                continue
            if isinstance(value, dict):
                sanitized_value = self._sanitize_for_hash(value)
                sanitized[key] = sanitized_value
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_for_hash(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


_frontend_snapshot_service: Optional[FrontendSnapshotPDFService] = None


def get_frontend_snapshot_pdf_service() -> FrontendSnapshotPDFService:
    global _frontend_snapshot_service
    if _frontend_snapshot_service is None:
        _frontend_snapshot_service = FrontendSnapshotPDFService()
    return _frontend_snapshot_service


def upsert_pdf_cache(
    db_session: Session,
    quote: Quote,
    payload: Dict[str, Any],
) -> QuotePDFCache:
    """Insert or update the PDF cache record for a quote."""

    def _apply_updates(target: QuotePDFCache) -> QuotePDFCache:
        target.pdf_path = payload.get("pdf_path", target.pdf_path)
        target.source = payload.get("source", target.source)
        target.file_size = payload.get("file_size", target.file_size)
        target.updated_at = datetime.utcnow()
        target.content_hash = payload.get("content_hash", target.content_hash)
        target.status = payload.get("status", target.status or 'ready')
        if payload.get("last_error") is not None:
            target.last_error = payload.get("last_error")
        elif target.status == 'ready':
            target.last_error = None
        return target

    cache = quote.pdf_cache

    if cache is None:
        cache = (
            db_session.query(QuotePDFCache)
            .filter(QuotePDFCache.quote_id == quote.id)
            .first()
        )

    try:
        if cache is None:
            cache = QuotePDFCache(
                quote_id=quote.id,
                pdf_path=payload.get("pdf_path"),
                source=payload.get("source", "playwright"),
                file_size=payload.get("file_size", 0),
                content_hash=payload.get("content_hash"),
                status=payload.get("status", "ready"),
                last_error=payload.get("last_error"),
            )
            db_session.add(cache)
            quote.pdf_cache = cache
        else:
            cache = _apply_updates(cache)

        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        cache = (
            db_session.query(QuotePDFCache)
            .filter(QuotePDFCache.quote_id == quote.id)
            .first()
        )

        if cache is None:
            raise

        cache = _apply_updates(cache)
        quote.pdf_cache = cache
        db_session.commit()

    db_session.refresh(cache)
    return cache
