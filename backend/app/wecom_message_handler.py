#!/usr/bin/env python3
"""
企业微信消息处理模块
处理接收的消息并生成回复
"""
import xml.etree.ElementTree as ET
import time
import hashlib
import requests
import json
from typing import Dict, Optional, Any, List
from datetime import datetime

class WeComMessage:
    """企业微信消息类"""
    
    def __init__(self, xml_data: str):
        """解析XML消息"""
        self.xml_data = xml_data
        self.root = ET.fromstring(xml_data)
        
        # 提取基本字段
        self.to_user_name = self._get_text('ToUserName')  # 企业微信CorpID
        self.from_user_name = self._get_text('FromUserName')  # 成员UserID
        self.create_time = self._get_text('CreateTime')
        self.msg_type = self._get_text('MsgType')
        self.agent_id = self._get_text('AgentID')
        
        # 根据消息类型提取特定字段
        if self.msg_type == 'text':
            self.content = self._get_text('Content')
            self.msg_id = self._get_text('MsgId')
        elif self.msg_type == 'event':
            self.event = self._get_text('Event')
            self.event_key = self._get_text('EventKey')
        
    def _get_text(self, tag: str) -> Optional[str]:
        """安全获取XML标签文本"""
        elem = self.root.find(tag)
        return elem.text if elem is not None else None


class MessageHandler:
    """消息处理器"""
    
    def __init__(self, corp_id: str):
        self.corp_id = corp_id
        self.commands = {
            '/help': self.handle_help,
            '/帮助': self.handle_help,
            '/查询': self.handle_search,
            '/search': self.handle_search,
            '/设备': self.handle_device,
            '/device': self.handle_device,
            '/供应商': self.handle_supplier,
            '/supplier': self.handle_supplier,
        }
    
    def process_message(self, decrypted_xml: str) -> str:
        """
        处理解密后的消息并返回回复
        
        Args:
            decrypted_xml: 解密后的XML消息
            
        Returns:
            回复的XML字符串
        """
        try:
            # 解析消息
            msg = WeComMessage(decrypted_xml)
            print(f"收到消息 - 类型: {msg.msg_type}, 来自: {msg.from_user_name}")
            
            # 根据消息类型处理
            if msg.msg_type == 'text':
                reply_content = self.handle_text_message(msg)
            elif msg.msg_type == 'event':
                reply_content = self.handle_event_message(msg)
            else:
                reply_content = f"暂不支持{msg.msg_type}类型的消息"
            
            # 构造回复消息
            return self.build_text_reply(msg.from_user_name, msg.to_user_name, reply_content)
            
        except Exception as e:
            print(f"处理消息时出错: {e}")
            return self.build_text_reply("", self.corp_id, "抱歉，处理您的消息时出现了错误。")
    
    def handle_text_message(self, msg: WeComMessage) -> str:
        """处理文本消息"""
        content = msg.content.strip()
        print(f"文本内容: {content}")
        
        # 检查是否是命令
        for cmd, handler in self.commands.items():
            if content.startswith(cmd):
                # 提取命令参数
                params = content[len(cmd):].strip()
                return handler(params)
        
        # 默认回复
        return self.handle_default(content)
    
    def handle_event_message(self, msg: WeComMessage) -> str:
        """处理事件消息"""
        if msg.event == 'subscribe':
            return self.handle_subscribe()
        elif msg.event == 'enter_agent':
            return self.handle_enter_agent()
        else:
            return f"收到事件: {msg.event}"
    
    def handle_help(self, params: str) -> str:
        """处理帮助命令"""
        help_text = """📋 芯片测试报价系统 - 命令帮助

可用命令：
• /帮助 或 /help - 显示此帮助信息
• /查询 [关键词] - 查询设备信息
• /设备 [名称] - 查看设备详情
• /供应商 - 查看所有供应商列表

示例：
• /查询 J750
• /设备 ETS-88
• /供应商

💡 提示：直接输入设备名称也可以进行查询"""
        return help_text
    
    def handle_search(self, params: str) -> str:
        """处理查询命令"""
        if not params:
            return "请提供查询关键词。例如：/查询 J750"
        
        try:
            # 调用API查询设备
            from app.config import settings
            api_base_url = settings.API_BASE_URL if hasattr(settings, 'API_BASE_URL') else "http://localhost:8000"
            response = requests.get(f'{api_base_url}/api/v1/machines/')
            if response.status_code == 200:
                machines = response.json()
                
                # 过滤匹配的设备
                matched = [m for m in machines if params.lower() in m['name'].lower()]
                
                if matched:
                    result = f"🔍 找到 {len(matched)} 个匹配的设备：\n\n"
                    for m in matched[:5]:  # 最多显示5个
                        supplier = m.get('supplier', {}).get('name', '未知')
                        rate = m.get('base_hourly_rate', 0)
                        currency = m.get('currency', 'RMB')
                        result += f"• {m['name']} - {supplier}\n"
                        result += f"  价格: {rate} {currency}/小时\n\n"
                    
                    if len(matched) > 5:
                        result += f"... 还有 {len(matched) - 5} 个结果"
                    return result
                else:
                    return f"未找到包含 \"{params}\" 的设备"
            else:
                return "查询失败，请稍后重试"
        except Exception as e:
            print(f"查询出错: {e}")
            return "查询服务暂时不可用"
    
    def handle_device(self, params: str) -> str:
        """处理设备查询命令"""
        if not params:
            return "请提供设备名称。例如：/设备 J750"
        
        try:
            # 调用API查询设备
            from app.config import settings
            api_base_url = settings.API_BASE_URL if hasattr(settings, 'API_BASE_URL') else "http://localhost:8000"
            response = requests.get(f'{api_base_url}/api/v1/machines/')
            if response.status_code == 200:
                machines = response.json()
                
                # 查找完全匹配的设备
                device = next((m for m in machines if m['name'].lower() == params.lower()), None)
                
                if device:
                    supplier = device.get('supplier', {})
                    supplier_name = supplier.get('name', '未知')
                    machine_type = supplier.get('machine_type', {}).get('name', '未知')
                    
                    result = f"📋 设备详情：{device['name']}\n\n"
                    result += f"• 供应商: {supplier_name}\n"
                    result += f"• 类型: {machine_type}\n"
                    result += f"• 基础价格: {device.get('base_hourly_rate', 0)} {device.get('currency', 'RMB')}/小时\n"
                    result += f"• 折扣率: {device.get('discount_rate', 1.0)}\n"
                    result += f"• 汇率: {device.get('exchange_rate', 1.0)}\n"
                    result += f"• 状态: {'激活' if device.get('active', False) else '未激活'}\n"
                    
                    if device.get('description'):
                        result += f"• 描述: {device['description']}\n"
                    
                    return result
                else:
                    # 模糊匹配
                    matched = [m for m in machines if params.lower() in m['name'].lower()]
                    if matched:
                        return f"未找到完全匹配的设备。\n\n您是否要查找：\n" + \
                               "\n".join([f"• {m['name']}" for m in matched[:3]])
                    else:
                        return f"未找到设备 \"{params}\""
            else:
                return "查询失败，请稍后重试"
        except Exception as e:
            print(f"查询出错: {e}")
            return "查询服务暂时不可用"
    
    def handle_supplier(self, params: str) -> str:
        """处理供应商查询命令"""
        try:
            # 调用API获取供应商列表
            from app.config import settings
            api_base_url = settings.API_BASE_URL if hasattr(settings, 'API_BASE_URL') else "http://localhost:8000"
            response = requests.get(f'{api_base_url}/api/v1/suppliers/')
            if response.status_code == 200:
                suppliers = response.json()
                
                result = "📦 供应商列表：\n\n"
                for idx, s in enumerate(suppliers, 1):
                    machine_type = s.get('machine_type', {}).get('name', '未知')
                    result += f"{idx}. {s['name']} - {machine_type}\n"
                
                return result
            else:
                return "获取供应商列表失败，请稍后重试"
        except Exception as e:
            print(f"查询出错: {e}")
            return "查询服务暂时不可用"
    
    def handle_default(self, content: str) -> str:
        """处理默认消息"""
        # 简单的关键词匹配
        if any(word in content.lower() for word in ['你好', 'hello', 'hi']):
            return "您好！欢迎使用芯片测试报价系统。\n\n输入 /帮助 查看可用命令。"
        elif any(word in content for word in ['谢谢', '感谢']):
            return "不客气！有其他问题随时询问。"
        else:
            # 当作设备名称进行查询
            return f"正在为您查询 \"{content}\" 相关信息...\n\n提示：输入 /帮助 查看所有可用命令。"
    
    def handle_subscribe(self) -> str:
        """处理关注事件"""
        return """🎉 欢迎使用芯片测试报价系统！

本系统可以帮助您：
• 查询测试设备信息
• 获取设备报价
• 查看供应商信息

输入 /帮助 开始使用"""
    
    def handle_enter_agent(self) -> str:
        """处理进入应用事件"""
        return "欢迎回来！输入 /帮助 查看可用命令。"
    
    def build_text_reply(self, to_user: str, from_user: str, content: str) -> str:
        """
        构造文本回复消息
        
        Args:
            to_user: 接收方UserID
            from_user: 发送方CorpID
            content: 回复内容
            
        Returns:
            XML格式的回复消息
        """
        create_time = int(time.time())
        
        xml_template = f"""<xml>
    <ToUserName><![CDATA[{to_user}]]></ToUserName>
    <FromUserName><![CDATA[{from_user}]]></FromUserName>
    <CreateTime>{create_time}</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[{content}]]></Content>
</xml>"""
        
        return xml_template