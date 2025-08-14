#!/usr/bin/env python3
"""
企业微信消息加解密模块
"""
import base64
import hashlib
import struct
import random
import string
from Crypto.Cipher import AES


def get_random_str(length=16):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def pkcs7_pad(data: bytes, block_size=32) -> bytes:
    """PKCS#7 填充"""
    padding_len = block_size - (len(data) % block_size)
    padding = bytes([padding_len] * padding_len)
    return data + padding


def pkcs7_unpad(data: bytes) -> bytes:
    """移除 PKCS#7 填充"""
    padding_len = data[-1]
    if padding_len < 1 or padding_len > 32:
        raise ValueError("Invalid PKCS#7 padding")
    return data[:-padding_len]


def encrypt_msg(reply_msg: str, aes_key: str, corp_id: str) -> str:
    """
    加密回复消息
    
    Args:
        reply_msg: 明文回复消息
        aes_key: AES密钥（43位）
        corp_id: 企业ID
        
    Returns:
        Base64编码的加密消息
    """
    # 准备AES密钥
    aes_key_bytes = base64.b64decode(aes_key + '=')
    iv = aes_key_bytes[:16]
    
    # 构造明文：16字节随机字符串 + 4字节网络序消息长度 + 消息 + CorpID
    random_str = get_random_str(16).encode('utf-8')
    msg_bytes = reply_msg.encode('utf-8')
    msg_len = struct.pack('>I', len(msg_bytes))
    corp_id_bytes = corp_id.encode('utf-8')
    
    # 拼接并填充
    plaintext = random_str + msg_len + msg_bytes + corp_id_bytes
    padded_plaintext = pkcs7_pad(plaintext)
    
    # AES加密
    cipher = AES.new(aes_key_bytes, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded_plaintext)
    
    # Base64编码
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_msg(encrypted_msg: str, aes_key: str) -> tuple[str, str]:
    """
    解密消息
    
    Args:
        encrypted_msg: Base64编码的加密消息
        aes_key: AES密钥（43位）
        
    Returns:
        (明文消息, 发送方CorpID)
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
    msg_len_bytes = decrypted_data[16:20]
    msg_len = struct.unpack('>I', msg_len_bytes)[0]
    
    # 提取消息内容
    msg_start = 20
    msg_end = msg_start + msg_len
    msg_content = decrypted_data[msg_start:msg_end].decode('utf-8')
    
    # 提取CorpID
    corp_id = decrypted_data[msg_end:].decode('utf-8')
    
    return msg_content, corp_id


def generate_signature(token: str, timestamp: str, nonce: str, encrypt_msg: str) -> str:
    """生成签名"""
    sorted_params = sorted([token, timestamp, nonce, encrypt_msg])
    sha1_str = ''.join(sorted_params)
    hash_obj = hashlib.sha1(sha1_str.encode('utf-8'))
    return hash_obj.hexdigest()


def verify_signature(token: str, timestamp: str, nonce: str, encrypt_msg: str, msg_signature: str) -> bool:
    """验证签名"""
    calculated_signature = generate_signature(token, timestamp, nonce, encrypt_msg)
    return calculated_signature == msg_signature