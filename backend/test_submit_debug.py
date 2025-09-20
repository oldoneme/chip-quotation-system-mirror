#!/usr/bin/env python3
"""
测试提交审批调试
"""

import requests
import json

def test_submit():
    """测试提交审批"""
    print("🧪 测试提交审批")

    # 使用现有的报价单ID 8进行测试（已经是pending状态）
    quote_id = 8

    try:
        response = requests.post(
            f"http://localhost:8000/api/v2/approval/{quote_id}/operate",
            json={
                "action": "submit",
                "comments": "测试状态同步",
                "channel": "auto"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"状态码: {response.status_code}")
        if response.text:
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except:
                print(f"响应文本: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_submit()