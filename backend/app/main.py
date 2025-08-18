import sys
import os
import hashlib
import base64
import struct
import time
import random
import xml.etree.ElementTree as ET
from typing import Optional

# 设置环境变量供认证模块使用（必须在导入之前设置）
os.environ["WECOM_CORP_ID"] = "ww3bf2288344490c5c"
os.environ["WECOM_AGENT_ID"] = "1000029"
os.environ["WECOM_CORP_SECRET"] = "Q_JcyrQIsTcBJON2S3JPFqTvrjVi-zHJDXFVQ2pYqNg"

# Add the project root directory to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, Query, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from Crypto.Cipher import AES
from app.database import engine, Base
from app.api.v1.api import api_router
from app.auth_routes import router as auth_router
from app.admin_routes import router as admin_router
from app.admin_management import router as admin_management_router
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

# 智能缓存中间件
@app.middleware("http")
async def smart_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    
    # HTML文件不缓存（确保每次都获取最新版本）
    if path == "/" or path.endswith(".html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Content-Type"] = "HTML"
    
    # 带哈希的静态资源长缓存（immutable，1年）
    elif "/static/" in path and any(path.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".svg", ".woff2", ".woff", ".ttf"]):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        response.headers["X-Content-Type"] = "Static"
    
    # API接口不缓存
    elif path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Content-Type"] = "API"
    
    # 其他资源短缓存（5分钟）
    else:
        response.headers["Cache-Control"] = "public, max-age=300"
        response.headers["X-Content-Type"] = "Other"
    
    # 添加版本标识
    response.headers["X-App-Version"] = "2024.8.14.2340"
    return response

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_management_router)

# 配置静态文件服务 (必须在所有API路由之后)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    # 为SPA应用提供fallback路由
    from fastapi.responses import FileResponse
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 排除API路径和特殊路径
        if full_path.startswith("api/") or full_path.startswith("auth/") or full_path.startswith("admin/") or full_path == "user-management":
            raise HTTPException(status_code=404, detail="Not found")
        
        # 检查静态文件是否存在
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # 否则返回index.html (SPA fallback)
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="Not found")

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

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
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