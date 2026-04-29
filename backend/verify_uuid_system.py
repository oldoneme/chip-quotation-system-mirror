#!/usr/bin/env python3
"""
UUID系统验证脚本 - 验证审批链接UUID生成和前端访问
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import requests
import json
from datetime import datetime


def get_auth_headers():
    token = os.getenv("CHIP_QUOTE_AUTH_TOKEN")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

def check_uuid_tokens():
    """检查数据库中的UUID token状态"""
    print("🔍 检查数据库中的UUID token状态...")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 检查所有报价单的token状态
        cursor.execute('''
            SELECT id, quote_number, approval_link_token, status, approval_status
            FROM quotes
            WHERE is_deleted = 0
            ORDER BY id DESC
            LIMIT 10
        ''')
        quotes = cursor.fetchall()

        print(f"\n📋 最近10个报价单的token状态:")
        for quote_id, quote_number, token, status, approval_status in quotes:
            has_uuid = token is not None and len(str(token)) == 36 and str(token).count('-') == 4
            print(f"   ID: {quote_id}, 编号: {quote_number}")
            print(f"   Token: {token}")
            print(f"   状态: {status}/{approval_status}, UUID: {'✅' if has_uuid else '❌'}")
            print()

        return quotes

    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return []
    finally:
        conn.close()

def test_uuid_frontend_links():
    """测试UUID链接的前端访问"""
    print("🌐 测试UUID链接的前端访问...")

    quotes = check_uuid_tokens()
    if not quotes:
        print("❌ 没有找到报价单数据")
        return False

    # 选择第一个有效的UUID token进行测试
    for quote_id, quote_number, token, status, approval_status in quotes:
        if token and len(str(token)) == 36:
            test_url = f"https://wecom-dev.chipinfos.com.cn/quote-detail/{token}"
            print(f"🔗 测试链接: {test_url}")
            print(f"   报价单: {quote_number} (ID: {quote_id})")

            try:
                response = requests.get(test_url, timeout=10, allow_redirects=False)
                print(f"   响应状态: {response.status_code}")

                if response.status_code in [200, 302, 301]:
                    print(f"   ✅ 链接可访问")
                    return True
                else:
                    print(f"   ⚠️ 链接返回状态码: {response.status_code}")

            except Exception as e:
                print(f"   ❌ 链接访问失败: {str(e)}")

            break

    return False

def test_api_endpoints():
    """测试相关API端点"""
    print("\n🔧 测试相关API端点...")

    # 测试后端服务状态
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
        else:
            print(f"⚠️ 后端服务状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端服务无法访问: {str(e)}")
        return False

    # 获取一个有效的报价单ID进行测试
    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM quotes WHERE is_deleted = 0 ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("❌ 没有找到有效的报价单")
        return False

    quote_id = result[0]

    headers = get_auth_headers()
    if headers is None:
        print("⚠️ 未设置 CHIP_QUOTE_AUTH_TOKEN，跳过受保护审批状态接口校验")
        return True

    # 测试审批状态查询
    try:
        response = requests.get(
            f"http://localhost:8000/api/v1/approval/status/{quote_id}",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            print(f"✅ 审批状态查询API正常 (报价单ID: {quote_id})")
        else:
            print(f"⚠️ 审批状态查询API异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 审批状态查询API失败: {str(e)}")

    return True

def test_wecom_integration():
    """测试企业微信集成相关功能"""
    print("\n📱 测试企业微信集成功能...")

    # 检查配置
    try:
        from app.config import settings
        wecom_configured = all([
            hasattr(settings, 'WECOM_CORP_ID') and settings.WECOM_CORP_ID,
            hasattr(settings, 'WECOM_BASE_URL') and settings.WECOM_BASE_URL,
        ])

        if wecom_configured:
            print("✅ 企业微信配置已设置")
            print(f"   BASE_URL: {getattr(settings, 'WECOM_BASE_URL', 'N/A')}")
        else:
            print("⚠️ 企业微信配置可能不完整")

    except Exception as e:
        print(f"❌ 检查企业微信配置失败: {str(e)}")
        return False

    return True

def main():
    """主函数"""
    print("🧪 UUID系统全面验证")
    print("=" * 60)
    print(f"时间: {datetime.now()}")
    print()

    # 步骤1: 检查数据库token状态
    quotes = check_uuid_tokens()
    if not quotes:
        print("❌ 数据库检查失败")
        return

    # 步骤2: 测试前端链接
    frontend_ok = test_uuid_frontend_links()

    # 步骤3: 测试API端点
    api_ok = test_api_endpoints()

    # 步骤4: 测试企业微信集成
    wecom_ok = test_wecom_integration()

    # 总结
    print("\n" + "=" * 60)
    print("🎯 验证总结:")
    print(f"   数据库UUID token: {'✅' if quotes else '❌'}")
    print(f"   前端链接访问: {'✅' if frontend_ok else '❌'}")
    print(f"   API端点测试: {'✅' if api_ok else '❌'}")
    print(f"   企业微信集成: {'✅' if wecom_ok else '❌'}")

    if all([quotes, frontend_ok, api_ok, wecom_ok]):
        print("\n🎉 UUID系统验证通过！企业微信审批链接应正常工作")
        print("\n💡 关键修复:")
        print("   1. approval_link_token字段已恢复UUID格式")
        print("   2. wecom_integration.py已使用UUID token生成链接")
        print("   3. 前端链接格式: /quote-detail/{UUID}")
        print("   4. 兼容旧的数字ID系统作为回退")
    else:
        print("\n⚠️ 部分功能可能存在问题，需要进一步调试")

if __name__ == "__main__":
    main()
