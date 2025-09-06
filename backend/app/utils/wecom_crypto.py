#!/usr/bin/env python3
"""
企业微信消息加密解密工具
严格按照企业微信官方文档实现AES-256-CBC加密解密
"""

import hashlib
import base64
import struct
from Crypto.Cipher import AES
from typing import Tuple


def wecom_signature(token: str, timestamp: str, nonce: str, fourth: str) -> str:
    """
    计算企业微信签名
    
    Args:
        token: 回调Token
        timestamp: 时间戳
        nonce: 随机数
        fourth: 第四个参数 (echostr 或 Encrypt)
        
    Returns:
        SHA1签名字符串
    """
    parts = [token, timestamp, nonce, fourth]
    parts.sort()
    return hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()


def _pkcs7_unpad(s: bytes) -> bytes:
    """
    PKCS#7去填充
    
    Args:
        s: 待去填充的字节串
        
    Returns:
        去填充后的字节串
        
    Raises:
        ValueError: 填充格式错误
    """
    if not s:
        raise ValueError("Empty data")
        
    pad = s[-1]
    if pad < 1 or pad > 32:
        raise ValueError(f"Bad padding: {pad}")
        
    # 检查填充是否正确
    for i in range(len(s) - pad, len(s)):
        if s[i] != pad:
            raise ValueError("Invalid padding")
            
    return s[:-pad]


def aes_key_iv(encoding_aes_key: str) -> Tuple[bytes, bytes]:
    """
    从EncodingAESKey生成AES密钥和初始向量
    
    Args:
        encoding_aes_key: 43位的EncodingAESKey
        
    Returns:
        (key, iv) 元组
        
    Raises:
        ValueError: 密钥长度不正确
    """
    # Base64解码并补等号
    key = base64.b64decode(encoding_aes_key + "=")
    
    if len(key) != 32:
        raise ValueError(f"AES key must be 32 bytes, got {len(key)}")
        
    iv = key[:16]  # 使用前16字节作为IV
    
    return key, iv


def wecom_decrypt(encoding_aes_key: str, encrypted_b64: str, expect_corp_id: str) -> bytes:
    """
    企业微信AES-256-CBC解密
    
    Args:
        encoding_aes_key: 43位的EncodingAESKey
        encrypted_b64: Base64编码的加密数据
        expect_corp_id: 期望的企业ID
        
    Returns:
        解密后的原始消息字节串
        
    Raises:
        ValueError: 解密失败或CorpID不匹配
    """
    try:
        # 获取密钥和IV
        key, iv = aes_key_iv(encoding_aes_key)
        
        # 创建AES解密器
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Base64解码加密数据
        encrypted_data = base64.b64decode(encrypted_b64)
        
        # AES解密
        decrypted_data = cipher.decrypt(encrypted_data)
        
        # PKCS#7去填充
        unpadded_data = _pkcs7_unpad(decrypted_data)
        
        # 解析企业微信消息结构：16字节随机 + 4字节长度 + 消息内容 + CorpID
        if len(unpadded_data) < 20:
            raise ValueError("Decrypted data too short")
            
        # 跳过前16字节随机数
        content = unpadded_data[16:]
        
        # 读取4字节大端长度
        if len(content) < 4:
            raise ValueError("Cannot read message length")
            
        msg_len = struct.unpack(">I", content[:4])[0]
        
        # 验证长度
        if len(content) < 4 + msg_len:
            raise ValueError(f"Message length mismatch: expected {msg_len}, available {len(content) - 4}")
            
        # 提取消息内容
        msg = content[4:4 + msg_len]
        
        # 提取并验证CorpID
        corp_id_bytes = content[4 + msg_len:]
        corp_id = corp_id_bytes.decode("utf-8")
        
        if corp_id != expect_corp_id:
            raise ValueError(f"CorpID mismatch: expected '{expect_corp_id}', got '{corp_id}'")
            
        return msg
        
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def wecom_encrypt(encoding_aes_key: str, msg: str, corp_id: str) -> str:
    """
    企业微信AES-256-CBC加密（用于测试）
    
    Args:
        encoding_aes_key: 43位的EncodingAESKey  
        msg: 要加密的消息字符串
        corp_id: 企业ID
        
    Returns:
        Base64编码的加密字符串
    """
    import os
    
    try:
        # 获取密钥和IV
        key, iv = aes_key_iv(encoding_aes_key)
        
        # 准备消息内容
        msg_bytes = msg.encode('utf-8')
        corp_id_bytes = corp_id.encode('utf-8')
        
        # 生成16字节随机数
        random_bytes = os.urandom(16)
        
        # 组装：16字节随机 + 4字节大端长度 + 消息内容 + CorpID
        msg_len = len(msg_bytes)
        content = random_bytes + struct.pack(">I", msg_len) + msg_bytes + corp_id_bytes
        
        # PKCS#7填充
        pad_len = 32 - (len(content) % 32)
        if pad_len == 32:
            pad_len = 0
        if pad_len > 0:
            padding = bytes([pad_len] * pad_len)
            content += padding
        
        # AES加密
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(content)
        
        # Base64编码
        return base64.b64encode(encrypted).decode('utf-8')
        
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")