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

# 设置环境变量供认证模块使用（必须在导入之前设置）
os.environ["WECOM_CORP_ID"] = "ww3bf2288344490c5c"
os.environ["WECOM_AGENT_ID"] = "1000029" 
os.environ["WECOM_CORP_SECRET"] = "Q_JcyrQIsTcBJON2S3JPFqTvrjVi-zHJDXFVQ2pYqNg"

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

from fastapi import FastAPI, Query, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from pydantic import ValidationError
from Crypto.Cipher import AES
from starlette.requests import Request as StarletteRequest

# 静态目录定位
PUBLIC_DIR = pathlib.Path(os.path.join(os.path.dirname(__file__), "..", "static")).resolve()
INDEX_FILE = PUBLIC_DIR / "index.html"

# 企业微信 UA 检测
WEWORK_UA_KEYS = ("wxwork", "wecom", "micromessenger")

def is_wework(req) -> bool:
    """检测是否是企业微信 WebView"""
    ua = (req.headers.get("user-agent") or "").lower()
    return any(k in ua for k in WEWORK_UA_KEYS)

def is_html_nav(req) -> bool:
    """判断是否为HTML导航请求"""
    p = req.url.path
    if p.startswith("/static/") or p.startswith("/assets/") or p.startswith("/api/") or p.startswith("/wecom/"):
        return False
    accept = req.headers.get("accept", "")
    has_ext = pathlib.Path(p).suffix != ""
    return ("text/html" in accept) or (p == "/") or (not has_ext) or p.endswith(".html")
from app.database import engine, Base
from app.api.v1.api import api_router
from app.auth_routes import router as auth_router
from app.admin_routes import router as admin_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.wecom_message_handler import MessageHandler
from app.wecom_crypto import encrypt_msg, decrypt_msg, generate_signature, verify_signature

# 设置日志
logger = setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
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
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

VERSION_PREFIX = f"/v/{APP_VERSION}"

# 强制路径版本化 + 302 重定向 + Clear-Site-Data 中间件
@app.middleware("http")
async def force_versioned_path_and_cache_headers(request: Request, call_next):
    try:
        p = request.url.path

        # 对 HTML 导航做路径版本化：如果不在 /v/<APP_VERSION>/ 下，或版本不匹配 → 302
        if is_html_nav(request):
            m = re.match(r"^/v/([^/]+)(/.*)?$", p)
            if not m or m.group(1) != APP_VERSION:
                rest = p
                if m:
                    rest = m.group(2) or "/"
                scheme, netloc = request.url.scheme, request.url.netloc
                q = dict(request.query_params)
                new_path = (f"{VERSION_PREFIX}" + (rest if rest.startswith("/") else f"/{rest}")).replace("//","/")
                new_url = urlunparse((scheme, netloc, new_path, "", urlencode(q, doseq=True), ""))
                resp = RedirectResponse(new_url, status_code=302)
                # 避免 302 被缓存
                resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
                resp.headers["Pragma"] = "no-cache"
                resp.headers["Expires"] = "0"
                if is_wework(request):
                    # 一次性清 webview 本地 cache/storage（不清 cookie，避免掉登录）
                    resp.headers["Clear-Site-Data"] = '"cache", "storage"'
                return resp

        resp = await call_next(request)

        # HTML 一律 no-store；静态文件长缓存
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

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(auth_router)
app.include_router(admin_router)

# 企业微信配置
WECOM_TOKEN = os.getenv("WECOM_TOKEN", "")
WECOM_AES_KEY = os.getenv("WECOM_AES_KEY", "")
WECOM_CORP_ID = os.getenv("WECOM_CORP_ID", "")


def pkcs7_unpad(data: bytes) -> bytes:
    """移除 PKCS#7 填充"""
    padding_len = data[-1]
    if padding_len < 1 or padding_len > 32:
        raise ValueError("Invalid PKCS#7 padding")
    return data[:-padding_len]

def verify_signature(token: str, timestamp: str, nonce: str, encrypt_msg: str, msg_signature: str) -> bool:
    """验证签名"""
    sorted_params = sorted([token, timestamp, nonce, encrypt_msg])
    sha1_str = ''.join(sorted_params)
    hash_obj = hashlib.sha1(sha1_str.encode('utf-8'))
    calculated_signature = hash_obj.hexdigest()
    return calculated_signature == msg_signature

def decrypt_msg(encrypted_msg: str, aes_key: str) -> tuple[str, str]:
    """
    解密消息
    返回: (明文消息, 发送方CorpID)
    """
    # Base64解码
    encrypted_data = base64.b64decode(encrypted_msg)
    
    # 准备AES密钥和IV
    aes_key_bytes = base64.b64decode(aes_key + '=')
    iv = aes_key_bytes[:16]
    
    # AES解密
    cipher = AES.new(aes_key_bytes, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(encrypted_data)
    
    # 去除PKCS#7填充
    decrypted_data = pkcs7_unpad(decrypted_data)
    
    # 解析明文结构：16字节随机字符串 + 4字节网络序消息长度 + 消息内容 + CorpID
    # 跳过前16字节随机字符串
    msg_len_bytes = decrypted_data[16:20]
    msg_len = struct.unpack('>I', msg_len_bytes)[0]
    
    # 提取消息内容
    msg_start = 20
    msg_end = msg_start + msg_len
    msg_content = decrypted_data[msg_start:msg_end].decode('utf-8')
    
    # 提取CorpID
    corp_id = decrypted_data[msg_end:].decode('utf-8')
    
    return msg_content, corp_id

@app.get("/wecom/callback")
async def wecom_callback_verify(
    msg_signature: Optional[str] = Query(None),
    timestamp: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None),
    echostr: Optional[str] = Query(None)
):
    """企业微信回调URL验证"""
    logger.info(f"GET /wecom/callback - msg_signature: {msg_signature}, timestamp: {timestamp}, nonce: {nonce}, echostr: {echostr}")
    
    # 检查必需参数
    if not all([msg_signature, timestamp, nonce, echostr]):
        logger.error("Missing required parameters")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    # 验证签名
    if not verify_signature(WECOM_TOKEN, timestamp, nonce, echostr, msg_signature):
        logger.error("Signature verification failed")
        raise HTTPException(status_code=403, detail="Signature verification failed")
    
    try:
        # 解密echostr
        plaintext, corp_id = decrypt_msg(echostr, WECOM_AES_KEY)
        
        # 验证CorpID
        if corp_id != WECOM_CORP_ID:
            logger.error(f"CorpID mismatch: expected {WECOM_CORP_ID}, got {corp_id}")
            raise HTTPException(status_code=400, detail="CorpID mismatch")
        
        logger.info(f"Successfully verified and decrypted echostr: {plaintext}")
        return Response(content=plaintext, media_type="text/plain")
    
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")

@app.post("/wecom/callback")
async def wecom_callback_event(
    request: Request,
    msg_signature: Optional[str] = Query(None),
    timestamp: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None)
):
    """企业微信事件回调"""
    logger.info(f"POST /wecom/callback - msg_signature: {msg_signature}, timestamp: {timestamp}, nonce: {nonce}")
    
    # 检查必需参数
    if not all([msg_signature, timestamp, nonce]):
        logger.error("Missing required parameters")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    try:
        # 读取请求体
        body = await request.body()
        body_str = body.decode('utf-8')
        logger.info(f"Request body: {body_str}")
        
        # 解析XML
        root = ET.fromstring(body_str)
        
        # 获取Encrypt字段（支持CDATA和非CDATA）
        encrypt_elem = root.find('Encrypt')
        if encrypt_elem is None:
            logger.error("Missing Encrypt field in XML")
            raise HTTPException(status_code=400, detail="Missing Encrypt field")
        
        encrypted_msg = encrypt_elem.text.strip()
        
        # 验证签名
        if not verify_signature(WECOM_TOKEN, timestamp, nonce, encrypted_msg, msg_signature):
            logger.error("Signature verification failed")
            raise HTTPException(status_code=403, detail="Signature verification failed")
        
        # 解密消息
        plaintext_xml, corp_id = decrypt_msg(encrypted_msg, WECOM_AES_KEY)
        
        # 验证CorpID
        if corp_id != WECOM_CORP_ID:
            logger.error(f"CorpID mismatch: expected {WECOM_CORP_ID}, got {corp_id}")
            raise HTTPException(status_code=400, detail="CorpID mismatch")
        
        # 打印解密后的XML
        logger.info(f"Decrypted XML:\n{plaintext_xml}")
        
        # 处理消息并生成回复
        handler = MessageHandler(WECOM_CORP_ID)
        reply_xml = handler.process_message(plaintext_xml)
        
        # 加密回复消息
        encrypted_reply = encrypt_msg(reply_xml, WECOM_AES_KEY, WECOM_CORP_ID)
        
        # 生成签名
        reply_nonce = str(random.randint(100000000, 999999999))
        reply_timestamp = str(int(time.time()))
        reply_signature = generate_signature(WECOM_TOKEN, reply_timestamp, reply_nonce, encrypted_reply)
        
        # 构造加密的回复XML
        response_xml = f"""<xml>
    <Encrypt><![CDATA[{encrypted_reply}]]></Encrypt>
    <MsgSignature><![CDATA[{reply_signature}]]></MsgSignature>
    <TimeStamp>{reply_timestamp}</TimeStamp>
    <Nonce><![CDATA[{reply_nonce}]]></Nonce>
</xml>"""
        
        logger.info(f"Sending encrypted reply")
        return Response(content=response_xml, media_type="application/xml")
    
    except ET.ParseError as e:
        logger.error(f"XML parsing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"XML parsing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Event processing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Event processing failed: {str(e)}")

@app.get("/test-route")
async def test_route():
    return {"message": "Test route works!"}

# 版本化路由：/v/<ver>/* 始终返回 index.html（由前端路由接管）
@app.get("/v/{ver}/")
@app.get("/v/{ver}/{path:path}")
def versioned_index(ver: str, path: str = ""):
    fp = INDEX_FILE
    if not fp.exists():
        return Response("index.html not found", status_code=404)
    resp = FileResponse(str(fp), media_type="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

# launch 路由：企业微信"主页 URL"可配置为 /launch
@app.get("/launch")
def launch():
    url = f"{VERSION_PREFIX}/"
    resp = RedirectResponse(url, status_code=302)
    resp.headers["Cache-Control"] = "no-store"
    return resp

# 保留原有的根路由作为兼容
@app.get("/")
async def root_html():
    fp = str(INDEX_FILE)
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
    logger.info(f"Starting {settings.APP_NAME} on port 8000")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )