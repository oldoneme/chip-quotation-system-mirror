#!/usr/bin/env python3
"""
获取企业微信审批模板的真实结构
"""

import requests
import json
import os

def get_access_token():
    """获取access_token"""
    corp_id = "ww3bf2288344490c5c"
    corp_secret = "Q_JcyrQIsTcBJON2S3JPFqTvrjVi-zHJDXFVQ2pYqNg"

    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={corp_secret}"
    response = requests.get(url)
    result = response.json()

    if result.get("errcode") == 0:
        return result.get("access_token")
    else:
        print(f"获取access_token失败: {result}")
        return None

def get_template_detail(template_id):
    """获取模板详细信息"""
    access_token = get_access_token()
    if not access_token:
        return None

    url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/gettemplatedetail?access_token={access_token}"
    data = {"template_id": template_id}

    response = requests.post(url, json=data)
    result = response.json()

    if result.get("errcode") == 0:
        print("✅ 获取模板结构成功")
        print(f"📝 模板ID: {template_id}")

        template_names = result.get("template_names", [])
        template_content = result.get("template_content", {})

        print(f"\n📄 模板名称: {template_names}")
        print(f"📋 模板内容:")

        controls = template_content.get("controls", [])
        print(f"🎛️  控件总数: {len(controls)}")

        for i, control in enumerate(controls):
            print(f"\n--- 控件 {i+1} ---")
            print(f"🆔 ID: {control.get('id')}")
            property_info = control.get('property', {})
            print(f"🎨 控件类型: {property_info.get('control')}")
            print(f"📜 标题: {property_info.get('title')}")
            print(f"🔧 完整属性: {json.dumps(property_info, ensure_ascii=False, indent=2)}")

        return controls
    else:
        print(f"❌ 获取模板结构失败: {result}")
        return None

if __name__ == "__main__":
    template_id = "C4c73QdXerFBuL6f2dEhgtbMYDpQFn82D1ifFmhyh"
    print(f"=== 获取模板 {template_id} 的结构 ===")

    controls = get_template_detail(template_id)

    if controls:
        print(f"\n🔧 推荐的apply_data结构:")
        print("contents = [")
        for i, control in enumerate(controls):
            control_id = control.get('id')
            control_type = control.get('property', {}).get('control')
            title = control.get('property', {}).get('title')

            if control_type == "Text":
                print(f'    {{')
                print(f'        "control": "Text",')
                print(f'        "id": "{control_id}",')
                print(f'        "title": [{{"text": "{title}", "lang": "zh_CN"}}],')
                print(f'        "value": {{"text": "报价单数据"}}')
                print(f'    }},')
            elif control_type == "Money":
                print(f'    {{')
                print(f'        "control": "Money",')
                print(f'        "id": "{control_id}",')
                print(f'        "title": [{{"text": "{title}", "lang": "zh_CN"}}],')
                print(f'        "value": {{"new_money": "100000"}}  # 分为单位')
                print(f'    }},')
            elif control_type == "Textarea":
                print(f'    {{')
                print(f'        "control": "Textarea",')
                print(f'        "id": "{control_id}",')
                print(f'        "title": [{{"text": "{title}", "lang": "zh_CN"}}],')
                print(f'        "value": {{"text": "多行文本内容"}}')
                print(f'    }},')
        print("]")

    print("\n🏁 分析完成")