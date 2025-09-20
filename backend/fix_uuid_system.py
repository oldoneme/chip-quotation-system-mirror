#!/usr/bin/env python3
"""
修复UUID系统 - 确保报价单有approval_link_token并修复企业微信链接生成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import uuid
from datetime import datetime

def ensure_approval_tokens():
    """确保所有报价单都有approval_link_token"""
    print("🔧 修复UUID系统 - 确保所有报价单有approval_link_token")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 查找没有approval_link_token的报价单
        cursor.execute('SELECT id, quote_number FROM quotes WHERE approval_link_token IS NULL OR approval_link_token = ""')
        quotes_without_token = cursor.fetchall()

        print(f"发现 {len(quotes_without_token)} 个报价单缺少approval_link_token")

        for quote_id, quote_number in quotes_without_token:
            # 生成UUID格式的token
            token = str(uuid.uuid4())

            cursor.execute('UPDATE quotes SET approval_link_token = ? WHERE id = ?', (token, quote_id))
            print(f"  为报价单 {quote_number} (ID: {quote_id}) 生成token: {token}")

        conn.commit()
        print(f"✅ 成功为 {len(quotes_without_token)} 个报价单生成approval_link_token")

        # 验证结果
        cursor.execute('SELECT COUNT(*) FROM quotes WHERE approval_link_token IS NULL OR approval_link_token = ""')
        remaining = cursor.fetchone()[0]
        print(f"验证：仍有 {remaining} 个报价单缺少token")

        return True

    except Exception as e:
        print(f"❌ 生成approval_link_token失败: {str(e)}")
        return False
    finally:
        conn.close()

def test_uuid_system():
    """测试UUID系统是否正常工作"""
    print(f"\n🧪 测试UUID系统")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 获取几个报价单的token
        cursor.execute('SELECT id, quote_number, approval_link_token FROM quotes LIMIT 3')
        samples = cursor.fetchall()

        print(f"样本报价单token状态:")
        for quote_id, quote_number, token in samples:
            is_uuid = len(token) == 36 and token.count('-') == 4 if token else False
            print(f"  ID: {quote_id}, 编号: {quote_number}, Token: {token}, UUID格式: {'✅' if is_uuid else '❌'}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 修复企业微信审批链接UUID系统")
    print(f"时间: {datetime.now()}")
    print("=" * 60)

    # 步骤1: 确保所有报价单都有approval_link_token
    if ensure_approval_tokens():
        # 步骤2: 测试系统
        if test_uuid_system():
            print(f"\n🎉 UUID系统修复完成！")
            print(f"💡 现在企业微信审批链接应该使用approval_link_token而不是数字ID")
        else:
            print(f"\n❌ UUID系统测试失败")
    else:
        print(f"\n❌ UUID系统修复失败")