#!/usr/bin/env python3
import os
import hashlib
import base64
import struct
import xml.etree.ElementTree as ET
from typing import Optional

from fastapi import FastAPI, Query, HTTPException, Response, Request
from Crypto.Cipher import AES

# 企业微信配置
WECOM_TOKEN = os.getenv("WECOM_TOKEN", "cN9bXxcD80")
WECOM_AES_KEY = os.getenv("WECOM_AES_KEY", "S1iZ8DxsKGpiL3b10oVpRm59FphYwKzhtdSCR18q3nl")
WECOM_CORP_ID = os.getenv("WECOM_CORP_ID", "ww3bf2288344490c")

app = FastAPI(title="企业微信回调服务")

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
    print(f"计算的签名: {calculated_signature}, 接收的签名: {msg_signature}")
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

@app.get("/")
async def root():
    return {"message": "企业微信回调服务运行中", "wecom_token": WECOM_TOKEN[:5] + "***"}

@app.get("/wecom/callback")
async def wecom_callback_verify(
    msg_signature: Optional[str] = Query(None),
    timestamp: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None),
    echostr: Optional[str] = Query(None)
):
    """企业微信回调URL验证"""
    print(f"GET /wecom/callback - 参数: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}, echostr={echostr}")
    
    # 检查必需参数
    if not all([msg_signature, timestamp, nonce, echostr]):
        print("ERROR: 缺少必需参数")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    # 验证签名
    if not verify_signature(WECOM_TOKEN, timestamp, nonce, echostr, msg_signature):
        print("ERROR: 签名验证失败")
        raise HTTPException(status_code=403, detail="Signature verification failed")
    
    try:
        # 解密echostr
        plaintext, corp_id = decrypt_msg(echostr, WECOM_AES_KEY)
        
        # 验证CorpID
        if corp_id != WECOM_CORP_ID:
            print(f"ERROR: CorpID不匹配: 期望 {WECOM_CORP_ID}, 收到 {corp_id}")
            raise HTTPException(status_code=400, detail="CorpID mismatch")
        
        print(f"SUCCESS: 验证并解密成功: {plaintext}")
        return Response(content=plaintext, media_type="text/plain")
    
    except Exception as e:
        print(f"ERROR: 解密失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")

@app.post("/wecom/callback")
async def wecom_callback_event(
    request: Request,
    msg_signature: Optional[str] = Query(None),
    timestamp: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None)
):
    """企业微信事件回调"""
    print(f"POST /wecom/callback - 参数: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}")
    
    # 检查必需参数
    if not all([msg_signature, timestamp, nonce]):
        print("ERROR: 缺少必需参数")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    try:
        # 读取请求体
        body = await request.body()
        body_str = body.decode('utf-8')
        print(f"请求体: {body_str}")
        
        # 解析XML
        root = ET.fromstring(body_str)
        
        # 获取Encrypt字段（支持CDATA和非CDATA）
        encrypt_elem = root.find('Encrypt')
        if encrypt_elem is None:
            print("ERROR: XML中缺少Encrypt字段")
            raise HTTPException(status_code=400, detail="Missing Encrypt field")
        
        encrypted_msg = encrypt_elem.text.strip()
        
        # 验证签名
        if not verify_signature(WECOM_TOKEN, timestamp, nonce, encrypted_msg, msg_signature):
            print("ERROR: 签名验证失败")
            raise HTTPException(status_code=403, detail="Signature verification failed")
        
        # 解密消息
        plaintext_xml, corp_id = decrypt_msg(encrypted_msg, WECOM_AES_KEY)
        
        # 验证CorpID
        if corp_id != WECOM_CORP_ID:
            print(f"ERROR: CorpID不匹配: 期望 {WECOM_CORP_ID}, 收到 {corp_id}")
            raise HTTPException(status_code=400, detail="CorpID mismatch")
        
        # 打印解密后的XML
        print(f"SUCCESS: 解密的XML:\n{plaintext_xml}")
        
        # 返回success表示成功接收
        return Response(content="success", media_type="text/plain")
    
    except ET.ParseError as e:
        print(f"ERROR: XML解析失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"XML parsing failed: {str(e)}")
    except Exception as e:
        print(f"ERROR: 事件处理失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Event processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print(f"启动企业微信回调服务:")
    print(f"  Token: {WECOM_TOKEN}")
    print(f"  AES Key: {WECOM_AES_KEY}")
    print(f"  Corp ID: {WECOM_CORP_ID}")
    uvicorn.run(app, host="0.0.0.0", port=8000)