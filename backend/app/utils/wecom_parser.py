#!/usr/bin/env python3
"""
企业微信回调事件健壮解析器
支持JSON和XML格式，多字段名兼容，容错处理
"""

import json
import xmltodict
from typing import Dict, Any, Optional, Union, List, Tuple


def parse_wecom_event(plain: Union[bytes, str]) -> Dict[str, Any]:
    """
    解析企业微信回调事件，支持JSON和XML格式
    
    输入：解密后的明文字节或字符串
    输出：规范化的事件dict，包含：
      - event: 事件类型
      - event_id: 事件ID（用于幂等）
      - sp_no: 审批单号
      - third_no: 第三方单号（报价单ID）
      - open_sp_status: 审批状态（1待审批 2已通过 3已拒绝 4已取消）
      - parser_path: 解析路径（用于调试）
    """
    if isinstance(plain, bytes):
        s = plain.decode("utf-8").strip()
    else:
        s = plain.strip()
    
    parser_path = []
    root = None
    
    # 1) 尝试JSON解析
    if s.startswith("{"):
        try:
            root = json.loads(s)
            parser_path.append("json")
        except Exception as e:
            parser_path.append(f"json_failed:{str(e)[:50]}")
    
    # 2) 尝试XML解析
    if root is None and ("<" in s):
        try:
            parsed_xml = xmltodict.parse(s)
            # xmltodict可能返回 {'xml': {...}} 或直接 {...}
            root = parsed_xml.get('xml', parsed_xml)
            parser_path.append("xml")
        except Exception as e:
            parser_path.append(f"xml_failed:{str(e)[:50]}")
    
    if root is None:
        return {
            "event": None,
            "event_id": None,
            "sp_no": None,
            "third_no": None,
            "open_sp_status": None,
            "parser_path": ";".join(parser_path),
            "raw_preview": s[:200] if s else ""
        }
    
    # 3) 提取字段（多路径兼容）
    result = {
        "event": _get_first(root, 
            ("Event",), ("event",), ("MsgType",)),
        
        "event_id": _get_first(root,
            ("EventID",), ("event_id",), ("EventId",), ("eventId",)),
        
        "sp_no": _get_first(root,
            ("ApprovalInfo", "SpNo"),
            ("approval_info", "sp_no"),
            ("SpNo",), ("sp_no",)),
        
        "third_no": _get_first(root,
            ("ApprovalInfo", "ThirdNo"),
            ("approval_info", "third_no"),
            ("ThirdNo",), ("third_no",)),
        
        "open_sp_status": _to_int(_get_first(root,
            ("ApprovalInfo", "OpenSpStatus"),
            ("ApprovalInfo", "SpStatus"),
            ("ApprovalInfo", "Status"),
            ("approval_info", "open_sp_status"),
            ("approval_info", "sp_status"),
            ("approval_info", "status"),
            ("OpenSpStatus",),
            ("SpStatus",),
            ("Status",),
            ("open_sp_status",),
            ("sp_status",),
            ("status",))),
        
        "parser_path": ";".join(parser_path)
    }
    
    # 4) 额外尝试提取其他可能有用的字段
    result["msg_type"] = _get_first(root, ("MsgType",), ("msg_type",))
    result["create_time"] = _get_first(root, ("CreateTime",), ("create_time",))
    result["from_user"] = _get_first(root, ("FromUserName",), ("from_user_name",))
    result["to_user"] = _get_first(root, ("ToUserName",), ("to_user_name",))
    
    # 如果有ApprovalInfo节点，尝试提取更多信息
    approval_info = _get_first(root, ("ApprovalInfo",), ("approval_info",))
    if approval_info and isinstance(approval_info, dict):
        result["sp_name"] = _get_first(approval_info, ("SpName",), ("sp_name",))
        result["apply_time"] = _get_first(approval_info, ("ApplyTime",), ("apply_time",))
        result["applyer"] = _get_first(approval_info, ("Applyer",), ("applyer",))
        
        # 尝试多种状态字段名
        if result["open_sp_status"] is None:
            for status_key in ["OpenSpStatus", "SpStatus", "Status", "open_sp_status", "sp_status", "status"]:
                if status_key in approval_info:
                    result["open_sp_status"] = _to_int(approval_info[status_key])
                    if result["open_sp_status"] is not None:
                        parser_path.append(f"status_from_approval_info.{status_key}")
                        break
    
    # 记录成功提取的字段
    extracted = []
    for k, v in result.items():
        if v is not None and k not in ["parser_path", "raw_preview"]:
            extracted.append(k)
    if extracted:
        parser_path.append(f"extracted:{','.join(extracted)}")
    
    result["parser_path"] = ";".join(parser_path)
    
    return result


def _get_first(root: Any, *paths: Tuple) -> Optional[Any]:
    """
    在多条备选路径里返回第一个命中的值
    路径可以是元组（多层级）或单个键名
    """
    if root is None:
        return None
        
    for path in paths:
        val = _dig(root, path)
        if val not in (None, "", [], {}):
            return val
    return None


def _dig(obj: Any, path: Tuple) -> Optional[Any]:
    """
    按路径深度提取值，支持大小写变体
    """
    cur = obj
    for key in path:
        if cur is None:
            return None
            
        # 处理dict类型
        if isinstance(cur, dict):
            # 尝试多种大小写变体
            found = False
            for k_variant in _key_variants(key):
                if k_variant in cur:
                    cur = cur[k_variant]
                    found = True
                    break
            
            if not found:
                return None
        # 处理list类型（取第一个元素继续）
        elif isinstance(cur, list) and len(cur) > 0:
            cur = cur[0]
            # 重新尝试当前key
            if isinstance(cur, dict):
                for k_variant in _key_variants(key):
                    if k_variant in cur:
                        cur = cur[k_variant]
                        break
                else:
                    return None
        else:
            return None
    
    # xmltodict可能把文本放在'#text'或'@value'
    if isinstance(cur, dict):
        if '#text' in cur:
            return cur['#text']
        elif '@value' in cur:
            return cur['@value']
        elif len(cur) == 1 and isinstance(list(cur.values())[0], str):
            # 只有一个字符串值的dict，直接返回该值
            return list(cur.values())[0]
    
    return cur


def _key_variants(key: str) -> List[str]:
    """
    生成键名的大小写变体
    """
    variants = [
        key,  # 原样
        key.lower(),  # 全小写
        key.upper(),  # 全大写
    ]
    
    # 驼峰和下划线转换
    if "_" in key:
        # snake_case -> camelCase
        parts = key.split("_")
        camel = parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
        pascal = "".join(p.capitalize() for p in parts)
        variants.extend([camel, pascal])
    else:
        # camelCase/PascalCase -> snake_case
        import re
        snake = re.sub(r'([A-Z])', r'_\1', key).lower().strip('_')
        if snake != key.lower():
            variants.append(snake)
    
    # 首字母大小写变体
    if len(key) > 0:
        variants.append(key[0].upper() + key[1:])
        variants.append(key[0].lower() + key[1:])
    
    # 去重并返回
    return list(dict.fromkeys(variants))


def _to_int(x: Any) -> Optional[int]:
    """
    安全转换为整数
    """
    if x is None:
        return None
    try:
        # 处理字符串、数字、布尔等
        if isinstance(x, bool):
            return 1 if x else 0
        return int(str(x).strip())
    except (ValueError, TypeError):
        return None


# 测试函数
if __name__ == "__main__":
    # 测试XML格式
    xml_sample = """
    <xml>
        <ToUserName><![CDATA[ww3bf2288344490c5c]]></ToUserName>
        <FromUserName><![CDATA[sys]]></FromUserName>
        <CreateTime>1757130248</CreateTime>
        <MsgType><![CDATA[event]]></MsgType>
        <Event><![CDATA[sys_approval_change]]></Event>
        <ApprovalInfo>
            <SpNo>202509060018</SpNo>
            <SpStatus>2</SpStatus>
            <ThirdNo>3</ThirdNo>
        </ApprovalInfo>
    </xml>
    """
    
    result = parse_wecom_event(xml_sample)
    print("XML解析结果:")
    for k, v in result.items():
        if v is not None:
            print(f"  {k}: {v}")
    
    # 测试JSON格式
    json_sample = """
    {
        "Event": "sys_approval_change",
        "EventID": "evt_123",
        "ApprovalInfo": {
            "SpNo": "202509060019",
            "OpenSpStatus": 3,
            "ThirdNo": "4"
        }
    }
    """
    
    result = parse_wecom_event(json_sample)
    print("\nJSON解析结果:")
    for k, v in result.items():
        if v is not None:
            print(f"  {k}: {v}")