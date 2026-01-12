import sys
import os
import hashlib
import base64
import struct
import time
import random
import xml.etree.ElementTree as ET
import subprocess
import datetime
import pathlib
import re
from typing import Optional
from urllib.parse import urlencode, urlunparse

# Add the project root directory to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 1) 确定当前版本标识（进程生命周期内稳定）
def _get_current_version() -> str:
    # 1) 环境指定
    v = os.getenv("APP_VERSION")
    if v:
        return v

    # 2) git 短 SHA（若部署环境有 .git）
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        if sha:
            return sha
    except Exception:
        pass

    # 3) 时间戳兜底
    return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")

APP_VERSION = _get_current_version()
print(f"🚀 启动应用，当前版本: {APP_VERSION}")

# 企业微信缓存解决方案配置
PUBLIC_DIR = pathlib.Path(os.path.join(os.path.dirname(__file__), "..", "static")).resolve()
INDEX_FILE = PUBLIC_DIR / "index.html"
WEWORK_UA_KEYS = ("wxwork", "wecom")
VERSION_PREFIX = f"/v/{APP_VERSION}"
MEDIA_DIR = pathlib.Path(os.path.join(os.path.dirname(__file__), "..", "media")).resolve()
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

def is_wework(req) -> bool:
    """检测是否是企业微信 WebView"""
    ua = (req.headers.get("user-agent") or "").lower()
    return any(k in ua for k in WEWORK_UA_KEYS)

def is_html_nav(req) -> bool:
    """判断是否为HTML导航请求"""
    p = req.url.path
    if (p.startswith("/static/") or p.startswith("/assets/") or p.startswith("/api/") or 
        p.startswith("/__") or p.startswith("/wecom/") or p.startswith("/auth/") or 
        p.startswith("/admin/") or p.startswith("/launch") or p.startswith("/clear-cache") or
        p.startswith("/dashboard") or p.startswith("/test-") or p.startswith("/cache-test")):
        return False
    accept = req.headers.get("accept", "")
    has_ext = pathlib.Path(p).suffix != ""
    return ("text/html" in accept) or (p == "/") or (not has_ext) or p.endswith(".html")

from fastapi import FastAPI, Query, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from pydantic import ValidationError
from Crypto.Cipher import AES
from starlette.requests import Request as StarletteRequest

# 3) HTML导航识别工具函数
HTML_EXTS = {".html", ""}

def is_html_navigation(req: StarletteRequest) -> bool:
    """
    判定是否是 HTML 导航请求：
    - Accept 含 text/html 或 mode==navigate
    - 路径没有扩展名或以 .html 结尾
    - 排除典型 API/静态资源/管理页面前缀
    """
    p = req.url.path
    # 扩展名
    import os
    ext = os.path.splitext(p)[1].lower()

    # 排除不应该重定向的路径
    excluded_paths = [
        "/static/", "/assets/", "/api/", "/__", 
        "/admin/", "/auth/", "/wecom/", "/dashboard", "/test-"
    ]
    
    if any(p.startswith(path) for path in excluded_paths):
        return False

    accept = req.headers.get("accept", "")
    if "text/html" in accept or ext in HTML_EXTS or p == "/":
        return True
    return False
from app.database import engine, Base
from app.api.v1.api import api_router
from app.api.v2.api import api_router as api_v2_router
from app.auth_routes import router as auth_router
from app.admin_routes import router as admin_router
from app.api.v1.admin.quotes import router as admin_quotes_router
from app.core.config import settings as core_settings
from app.config import settings as runtime_settings
from app.core.logging import setup_logging
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
# 企业微信相关功能已移至专门的模块处理

# 设置日志
logger = setup_logging()

missing_wecom_keys = [
    key for key in [
        "WECOM_CORP_ID",
        "WECOM_AGENT_ID",
        "WECOM_SECRET",
        "WECOM_CALLBACK_TOKEN",
        "WECOM_ENCODING_AES_KEY",
    ]
    if not getattr(runtime_settings, key, None)
]

if missing_wecom_keys:
    logger.warning(
        "企业微信配置缺失，将跳过相关功能：%s",
        ", ".join(missing_wecom_keys),
    )

# === INJECTED: MANUAL_DB_TABLE_CREATION ===
# 在调试模式下自动创建SQLite数据表，但现在仅在显式配置开启时才执行
# 这有助于避免在无需初始化时意外修改或重新创建数据库表
if runtime_settings.AUTO_CREATE_DB_TABLES_ON_STARTUP:
    logger.info("配置开启：在启动时自动创建数据库表 (AUTO_CREATE_DB_TABLES_ON_STARTUP=True)")
    Base.metadata.create_all(bind=engine)
elif runtime_settings.DEBUG and runtime_settings.DATABASE_URL.startswith("sqlite"):
    logger.info("调试模式下，但未开启 AUTO_CREATE_DB_TABLES_ON_STARTUP，跳过自动建表。")
# === END INJECTED ===

app = FastAPI(
    title=core_settings.APP_NAME,
    version=core_settings.APP_VERSION,
    debug=core_settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 添加异常处理器
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=core_settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix=core_settings.API_V1_STR)
app.include_router(api_v2_router, prefix="/api")  # V2 API: /api/v2/
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_quotes_router, prefix=core_settings.API_V1_STR + "/admin")

# 企业微信强校验回调路由 - 唯一安全入口
from fastapi import Query, Request, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.v1.endpoints.wecom_callback import verify_callback_url, handle_approval_callback

@app.get("/wecom/callback")
async def wecom_secure_callback_verify(
    msg_signature: str = Query(...),
    timestamp: str = Query(...), 
    nonce: str = Query(...),
    echostr: str = Query(...),
    db: Session = Depends(get_db)
):
    """企业微信强校验回调URL验证 - 唯一安全入口"""
    return await verify_callback_url(msg_signature, timestamp, nonce, echostr, db)

@app.post("/wecom/callback") 
async def wecom_secure_callback_handle(
    request: Request,
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...), 
    db: Session = Depends(get_db)
):
    """企业微信强校验回调处理 - 唯一安全入口"""
    return await handle_approval_callback(request, msg_signature, timestamp, nonce, db)

# 生产环境安全状态检查端点
@app.get("/wecom-security-check")
async def wecom_security_check():
    """企业微信回调安全配置检查"""
    return {
        "message": "企业微信回调安全配置检查",
        "active_endpoint": {
            "/wecom/callback": "✅ 唯一安全入口，强校验启用"
        },
        "security_features": {
            "signature_verification": "✅ 严格验证，失败即拒绝",
            "aes_encryption": "✅ 标准AES-256-CBC解密", 
            "debug_bypass": "❌ 已完全移除",
            "idempotent_processing": "✅ EventID唯一性保证",
            "error_monitoring": "✅ 完整日志和告警"
        },
        "database_integrity": {
            "event_id_unique": "✅ approval_timeline.event_id UNIQUE",
            "sp_no_unique": "✅ 审批实例唯一性保证",
            "transaction_commit": "✅ 原子性事务处理"
        },
        "status_mapping": {
            "1": "pending (审批中)",
            "2": "approved (已通过)",
            "3": "rejected (已拒绝)",
            "4": "cancelled (已取消)"
        },
        "configuration": f"{runtime_settings.WECOM_BASE_URL}/wecom/callback"
    }

@app.get("/test-route")
async def test_route():
    return {"message": "Test route works!"}

@app.get("/cache-test.html")
async def cache_test_page():
    """缓存测试页面"""
    fp = os.path.join(PUBLIC_DIR, "cache-test.html")
    if os.path.exists(fp):
        resp = FileResponse(fp, media_type="text/html; charset=utf-8")
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    return {"error": "cache-test.html not found"}

# 5) 显式HTML路由确保no-store
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

@app.get("/")
async def root_html():
    fp = os.path.join(PUBLIC_DIR, "index.html")
    resp = FileResponse(fp, media_type="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    resp.headers["X-App-Version"] = APP_VERSION
    resp.headers["X-Content-Type"] = "HTML-Direct-Route"
    return resp

@app.get("/index.html")
async def index_html():
    return await root_html()

# 添加静态文件服务
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

@app.get("/dashboard")
async def dashboard():
    """权限控制仪表盘页面"""
    return FileResponse('static/dashboard.html')

@app.get("/test-permissions")
async def test_permissions():
    """权限系统测试页面"""
    return FileResponse('static/test-permissions.html')

@app.get("/__version")
def get_version():
    """版本检测端点 - 统一返回结构"""
    return JSONResponse({
        "version": APP_VERSION,
        "buildTime": os.getenv("BUILD_TIME", datetime.datetime.utcnow().isoformat()),
        "git": os.getenv("GIT_SHA", APP_VERSION)
    })

@app.get("/clear-cache")
async def clear_cache():
    """强制清除缓存并重新生成页面"""
    import time
    import hashlib
    from datetime import datetime
    
    # 生成新的版本号
    timestamp = str(int(time.time()))
    version_hash = hashlib.md5(f'{datetime.now().isoformat()}'.encode()).hexdigest()[:8]
    
    # 读取当前HTML
    with open('static/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 更新版本号
    import re
    html = re.sub(r'main\.293d4e25\.js\?v=[a-f0-9]{8}', f'main.293d4e25.js?v={version_hash}', html)
    html = re.sub(r'main\.f08f903d\.css\?v=[a-f0-9]{8}', f'main.f08f903d.css?v={version_hash}', html)
    html = re.sub(r'无缓存版[a-f0-9]{8}', f'无缓存版{version_hash}', html)
    
    # 写回文件
    with open('static/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    return {
        "message": "缓存已清理",
        "new_version": version_hash,
        "timestamp": timestamp,
        "clear_instructions": [
            "1. 关闭企业微信应用",
            "2. 等待10秒",  
            "3. 重新打开企业微信应用",
            "4. 如果仍有缓存，手动刷新页面"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {core_settings.APP_NAME} on port 8000")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=core_settings.DEBUG,
        log_level=core_settings.LOG_LEVEL.lower()
    )

# === injected:middleware-force-version ===

@app.middleware("http")
async def force_versioned_path_and_cache_headers(request: Request, call_next):
    try:
        p = request.url.path
        
        if is_html_nav(request):
            m = re.match(r"^/v/([^/]+)(/.*)?$", p)
            if not m:
                # 非版本化路径，需要重定向到版本化路径
                scheme, netloc = request.url.scheme, request.url.netloc
                q = dict(request.query_params)
                new_path = (f"{VERSION_PREFIX}" + (p if p.startswith("/") else f"/{p}")).replace("//","/")
                new_url = urlunparse((scheme, netloc, new_path, "", urlencode(q, doseq=True), ""))
                resp = RedirectResponse(new_url, status_code=302)
                resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
                resp.headers["Pragma"] = "no-cache"
                resp.headers["Expires"] = "0"
                if is_wework(request):
                    resp.headers["Clear-Site-Data"] = '"cache", "storage"'
                return resp
            elif m.group(1) != APP_VERSION:
                # 版本化路径但版本不匹配，需要重定向到正确版本
                rest = m.group(2) or "/"
                scheme, netloc = request.url.scheme, request.url.netloc
                q = dict(request.query_params)
                new_path = f"{VERSION_PREFIX}{rest}"
                new_url = urlunparse((scheme, netloc, new_path, "", urlencode(q, doseq=True), ""))
                resp = RedirectResponse(new_url, status_code=302)
                resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
                resp.headers["Pragma"] = "no-cache"
                resp.headers["Expires"] = "0"
                if is_wework(request):
                    resp.headers["Clear-Site-Data"] = '"cache", "storage"'
                return resp
            # else: 正确的版本化路径，继续处理

        resp = await call_next(request)

        if is_html_nav(request):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            if is_wework(request):
                resp.headers.setdefault("Clear-Site-Data", '"cache", "storage"')
        else:
            path = request.url.path
            if (path.startswith("/static/") or path.startswith("/assets/")) and (path.endswith(".js") or path.endswith(".css")):
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"

        return resp
    except Exception:
        r = Response("Internal Error", status_code=500)
        r.headers["Cache-Control"] = "no-store"
        return r



# === injected:versioned-index ===

@app.get("/v/{ver}/")
@app.head("/v/{ver}/")
@app.get("/v/{ver}/{path:path}")
@app.head("/v/{ver}/{path:path}")
async def versioned_index(ver: str, path: str = ""):
    fp = INDEX_FILE
    if not fp.exists():
        return Response("index.html not found", status_code=404)
    resp = FileResponse(str(fp), media_type="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp



# === injected:launch-route ===

@app.get("/launch")
def launch():
    url = f"{VERSION_PREFIX}/"
    resp = RedirectResponse(url, status_code=302)
    resp.headers["Cache-Control"] = "no-store"
    return resp
