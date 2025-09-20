#!/usr/bin/env python3
"""
测试环境变量加载
"""

import os
import sys

# 添加path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_env():
    """直接测试环境变量"""
    print("🔍 直接测试环境变量:")
    api_base_url = os.getenv("API_BASE_URL")
    print(f"   API_BASE_URL = {api_base_url}")
    return api_base_url

def test_with_dotenv():
    """使用dotenv加载后测试"""
    print("\n🔍 使用dotenv加载后测试:")
    try:
        from dotenv import load_dotenv

        # 加载.env文件
        env_loaded = load_dotenv()
        print(f"   dotenv加载结果: {env_loaded}")

        api_base_url = os.getenv("API_BASE_URL")
        print(f"   API_BASE_URL = {api_base_url}")
        return api_base_url
    except ImportError:
        print("   ❌ python-dotenv未安装")
        return None

def test_service_url_generation():
    """测试服务中的URL生成"""
    print("\n🔍 测试服务中的URL生成:")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        # 模拟_get_quote_detail_url方法的逻辑
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        print(f"   获取到的API_BASE_URL: {api_base_url}")

        quote_id = 26

        # 使用相同的逻辑生成URL
        if api_base_url.endswith('/api'):
            detail_url = f"{api_base_url}/v1/wecom-approval/quote-detail-redirect/{quote_id}"
        else:
            detail_url = f"{api_base_url}/api/v1/wecom-approval/quote-detail-redirect/{quote_id}"

        print(f"   生成的URL: {detail_url}")
        return detail_url

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return None

def check_env_file():
    """检查.env文件内容"""
    print("\n🔍 检查.env文件内容:")
    env_path = ".env"

    if os.path.exists(env_path):
        print(f"   .env文件存在: {os.path.abspath(env_path)}")
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                if 'API_BASE_URL' in line:
                    print(f"   找到配置: {line.strip()}")
                    break
            else:
                print("   ❌ 未找到API_BASE_URL配置")
        except Exception as e:
            print(f"   ❌ 读取.env文件失败: {e}")
    else:
        print("   ❌ .env文件不存在")

if __name__ == "__main__":
    print("🚀 测试环境变量加载和URL生成")
    print("=" * 50)

    check_env_file()
    direct_result = test_direct_env()
    dotenv_result = test_with_dotenv()
    url_result = test_service_url_generation()

    print("\n" + "=" * 50)
    print("📊 测试总结:")
    print(f"  直接环境变量: {'✅' if direct_result and 'localhost' not in direct_result else '❌'}")
    print(f"  dotenv加载后: {'✅' if dotenv_result and 'localhost' not in dotenv_result else '❌'}")
    print(f"  生成的URL: {'✅' if url_result and 'localhost' not in url_result else '❌'}")

    if url_result and 'localhost' in url_result:
        print("\n💡 问题诊断: 环境变量未正确加载，仍在使用默认的localhost")
        print("   建议: 确保应用启动时正确加载了.env文件")