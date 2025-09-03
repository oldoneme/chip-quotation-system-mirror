#!/usr/bin/env python3
"""
企业微信回调配置测试工具
用于测试和验证企业微信回调URL配置和签名验证
"""

import hashlib
import time
import requests
import json
from datetime import datetime

# 配置信息（这些需要在企业微信后台配置）
TEST_TOKEN = "cN9bXxcD80"  # 企业微信后台真实配置的Token
BASE_URL = "http://127.0.0.1:8000/api/v1/wecom-callback"

def generate_signature(token: str, timestamp: str, nonce: str, echostr: str = None) -> str:
    """生成企业微信回调签名"""
    if echostr:
        sign_list = [token, timestamp, nonce, echostr]
    else:
        sign_list = [token, timestamp, nonce]
    
    sign_list.sort()
    sign_str = "".join(sign_list)
    
    return hashlib.sha1(sign_str.encode()).hexdigest()

def test_callback_verify():
    """测试回调URL验证"""
    print("🧪 测试企业微信回调URL验证...")
    
    timestamp = str(int(time.time()))
    nonce = "random_nonce_123"
    echostr = "test_echo_string"
    
    # 生成正确的签名
    signature = generate_signature(TEST_TOKEN, timestamp, nonce, echostr)
    
    print(f"   生成的签名: {signature}")
    print(f"   时间戳: {timestamp}")
    print(f"   随机数: {nonce}")
    print(f"   回显字符串: {echostr}")
    
    # 测试验证端点
    url = f"{BASE_URL}/verify"
    params = {
        "msg_signature": signature,
        "timestamp": timestamp,
        "nonce": nonce,
        "echostr": echostr
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ 回调验证成功！返回: {response.text}")
            if response.text == echostr:
                print("✅ echostr 验证正确")
                return True
            else:
                print(f"❌ echostr 不匹配: 期望 '{echostr}', 实际 '{response.text}'")
        else:
            print(f"❌ 回调验证失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
    
    return False

def check_current_environment():
    """检查当前环境配置"""
    print("\n🔍 检查当前环境配置...")
    
    # 检查配置
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        from app.config import settings
        
        print(f"   WECOM_CALLBACK_TOKEN: {'已配置' if settings.WECOM_CALLBACK_TOKEN else '未配置'}")
        if settings.WECOM_CALLBACK_TOKEN:
            print(f"   实际Token: {settings.WECOM_CALLBACK_TOKEN[:10]}...")
        print(f"   WECOM_CORP_ID: {'已配置' if settings.WECOM_CORP_ID else '未配置'}")
        print(f"   WECOM_SECRET: {'已配置' if settings.WECOM_SECRET else '未配置'}")
        
        if not settings.WECOM_CALLBACK_TOKEN:
            print("⚠️  警告: WECOM_CALLBACK_TOKEN 未配置，回调验证会失败")
            print(f"   建议设置环境变量: export WECOM_CALLBACK_TOKEN='{TEST_TOKEN}'")
            return False
        return True
    
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

def main():
    print("="*60)
    print("企业微信回调配置测试工具")
    print("="*60)
    
    # 检查环境
    env_ok = check_current_environment()
    
    if not env_ok:
        print("\n❌ 环境配置有问题，无法继续测试")
        return
    
    print("\n📋 企业微信回调配置信息:")
    print(f"   回调验证URL: {BASE_URL}/verify")
    print(f"   审批回调URL: {BASE_URL}/approval")
    print(f"   消息回调URL: {BASE_URL}/message")
    print(f"   真实配置URL: http://127.0.0.1:8000/wecom/callback")
    print(f"   测试Token: {TEST_TOKEN}")
    
    # 测试验证URL
    verify_success = test_callback_verify()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()
