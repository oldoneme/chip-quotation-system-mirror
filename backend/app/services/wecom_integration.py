"""
企业微信审批集成服务
处理企业微信审批流程的核心功能
"""

import json
import time
import hashlib
import secrets
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Quote, ApprovalRecord, User
from ..database import get_db
from ..config import settings


class WeComApprovalIntegration:
    """企业微信审批集成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.corp_id = settings.WECOM_CORP_ID
        self.agent_id = settings.WECOM_AGENT_ID
        self.secret = settings.WECOM_SECRET
        self.approval_template_id = settings.WECOM_APPROVAL_TEMPLATE_ID
        self.callback_url = settings.WECOM_CALLBACK_URL
        self._access_token = None
        self._token_expires_at = None
        
    async def get_access_token(self) -> str:
        """获取企业微信access_token"""
        # 检查缓存的token是否有效
        if self._access_token and self._token_expires_at:
            if time.time() < self._token_expires_at:
                return self._access_token
        
        # 获取新的access_token
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
        if data.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"获取企业微信access_token失败: {data.get('errmsg')}"
            )
        
        self._access_token = data["access_token"]
        # Token有效期为7200秒，提前5分钟刷新
        self._token_expires_at = time.time() + data["expires_in"] - 300
        
        return self._access_token
    
    async def upload_temp_file(self, content: str, filename: str = "quote_detail.txt") -> str:
        """上传临时文件到企业微信获取media_id"""
        access_token = await self.get_access_token()
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=file"
        
        files = {
            'media': (filename, content.encode('utf-8'), 'text/plain')
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, files=files)
            result = response.json()
            
        if result.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {result.get('errmsg')}"
            )
            
        return result["media_id"]
    
    async def submit_quote_approval(self, quote_id: int, approver_userid: str = None) -> Dict:
        """
        提交报价单到企业微信审批
        使用模板定义的审批人，简化流程
        
        Args:
            quote_id: 报价单ID
            approver_userid: 可选的审批人ID（如果不使用模板审批人）
            
        Returns:
            审批申请创建结果
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")
        
        access_token = await self.get_access_token()
        
        # 生成报价单详情的企业微信应用内链接
        # 使用企业微信OAuth认证自动跳转到报价单详情页
        base_url = self.callback_url if self.callback_url else "http://127.0.0.1:8000"
        oauth_redirect_url = f"{base_url}/api/v1/auth/callback"
        detail_state = f"quote_detail_{quote.id}"
        
        # 构建企业微信OAuth链接，点击后直接在企业微信内打开应用
        detail_link = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={self.corp_id}&redirect_uri={oauth_redirect_url}&response_type=code&scope=snsapi_base&state={detail_state}#wechat_redirect"
        
        # 构建简洁的描述信息（由于Text字段长度限制）
        description_with_link = f"{quote.description or ''}。💰总金额¥{quote.total_amount:.2f}。📋详情链接见附件"
        
        # 创建简洁的链接文件
        link_file_content = f"报价单详情链接：\n{detail_link}\n\n点击上方链接查看详情"
        media_id = await self.upload_temp_file(link_file_content, f"{quote.quote_number}_链接.txt")
        
        # 构建审批申请数据 - 使用真实的模板字段ID
        approval_data = {
            "creator_userid": quote.creator.userid if quote.creator else "",
            "template_id": self.approval_template_id,
            "use_template_approver": 1,  # 使用模板中定义的审批人
            "third_no": str(quote.id),  # 添加第三方单号用于回调映射
            "apply_data": {
                "contents": [
                    {"control": "Text", "id": "Text-1756706105289", "value": {"text": quote.quote_type or "标准报价"}},
                    {"control": "Text", "id": "Text-1756705975378", "value": {"text": quote.quote_number}},
                    {"control": "Text", "id": "Text-1756706001498", "value": {"text": quote.customer_name}},
                    {"control": "Text", "id": "Text-1756706160253", "value": {"text": description_with_link}},
                    {"control": "File", "id": "File-1756706130702", "value": {"files": [{"file_id": media_id}]}},
                    {"control": "File", "id": "File-1756709748491", "value": {"files": []}}
                ]
            }
        }
        
        # 如果指定了审批人，覆盖模板设置
        if approver_userid:
            approval_data["use_template_approver"] = 0
            approval_data["approver"] = [{
                "attr": 2,
                "userid": [approver_userid]
            }]
        
        # 发送审批申请
        url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/applyevent?access_token={access_token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=approval_data)
            result = response.json()
            
        if result.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"提交审批失败: {result.get('errmsg', 'Unknown error')}"
            )
        
        # 保存审批ID到报价单
        quote.wecom_approval_id = result["sp_no"]
        quote.approval_status = "pending"
        
        # 保存审批实例映射（用于回调时查找）
        import sqlite3
        conn = sqlite3.connect('app/test.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO approval_instance 
            (quotation_id, sp_no, third_no, status) 
            VALUES (?, ?, ?, ?)
        """, (quote.id, result["sp_no"], str(quote.id), "pending"))
        conn.commit()
        conn.close()
        
        self.db.commit()
        
        return {
            "success": True,
            "sp_no": result["sp_no"],
            "message": "审批申请已提交"
        }
    
    async def get_approval_detail(self, sp_no: str) -> Dict:
        """
        获取审批单详情
        
        Args:
            sp_no: 审批单号
            
        Returns:
            审批单详情
        """
        access_token = await self.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovaldetail?access_token={access_token}"
        
        data = {"sp_no": sp_no}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            result = response.json()
            
        if result.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"获取审批详情失败: {result.get('errmsg')}"
            )
        
        return result
    
    async def send_approval_notification(
        self, 
        quote_id: int, 
        approver_userid: str,
        message_type: str = "pending"
    ) -> bool:
        """
        发送审批通知消息
        
        Args:
            quote_id: 报价单ID
            approver_userid: 接收人的企业微信userid
            message_type: 消息类型 (pending/approved/rejected)
            
        Returns:
            是否发送成功
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return False
        
        access_token = await self.get_access_token()
        
        # 生成企业微信应用内链接，直接跳转到报价单详情页面
        # 使用企业微信的应用跳转协议
        app_url = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={self.corp_id}&redirect_uri={self.callback_url}/auth/callback&response_type=code&scope=snsapi_base&state=quote_detail_{quote_id}"
        
        # 如果有审批链接token，也可以提供备用链接
        if hasattr(quote, 'approval_link_token') and quote.approval_link_token:
            approval_url = f"{self.callback_url}/approval/{quote.approval_link_token}"
        else:
            approval_url = app_url
        
        # 根据消息类型构建不同的消息内容
        messages = {
            "pending": {
                "title": "待审批提醒",
                "description": f"您有新的报价单待审批\\n报价单号：{quote.quote_number}\\n客户：{quote.customer_name}\\n金额：¥{quote.total_amount:.2f}",
                "btntxt": "立即审批"
            },
            "approved": {
                "title": "审批已通过",
                "description": f"报价单已审批通过\\n报价单号：{quote.quote_number}\\n审批时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "btntxt": "查看详情"
            },
            "rejected": {
                "title": "审批已拒绝",
                "description": f"报价单审批被拒绝\\n报价单号：{quote.quote_number}\\n请查看拒绝原因",
                "btntxt": "查看详情"
            }
        }
        
        msg_content = messages.get(message_type, messages["pending"])
        
        # 构建文本卡片消息
        message_data = {
            "touser": approver_userid,
            "msgtype": "textcard",
            "agentid": self.agent_id,
            "textcard": {
                "title": msg_content["title"],
                "description": msg_content["description"],
                "url": approval_url,
                "btntxt": msg_content["btntxt"]
            }
        }
        
        # 发送消息
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=message_data)
            result = response.json()
            
        return result.get("errcode") == 0
    
    async def handle_approval_callback(self, callback_data: Dict) -> bool:
        """
        处理企业微信审批回调
        
        Args:
            callback_data: 回调数据
            
        Returns:
            处理是否成功
        """
        try:
            # 解析回调数据
            sp_status = callback_data.get("ApprovalInfo", {}).get("SpStatus")
            sp_no = callback_data.get("ApprovalInfo", {}).get("SpNo")
            
            if not sp_no:
                return False
            
            # 查找对应的报价单
            quote = self.db.query(Quote).filter(
                Quote.wecom_approval_id == sp_no
            ).first()
            
            if not quote:
                return False
            
            # 更新审批状态
            status_mapping = {
                1: "pending",     # 审批中
                2: "approved",    # 已通过
                3: "rejected",    # 已拒绝
                4: "cancelled"    # 已撤销
            }
            
            new_status = status_mapping.get(sp_status)
            if new_status:
                quote.approval_status = new_status
                
                # 更新报价单状态和时间
                if new_status == "approved":
                    quote.status = "approved"  # 更新报价单状态为已批准
                    quote.approved_at = datetime.now()
                elif new_status == "rejected":
                    quote.status = "rejected"  # 更新报价单状态为已拒绝
                    quote.approved_at = datetime.now()
                    
                # 暂时绕过审批记录创建，直接使用SQL插入避免字段不匹配
                try:
                    # 使用原生SQL插入审批记录，只使用存在的字段
                    from sqlalchemy import text
                    self.db.execute(text("""
                        INSERT INTO approval_records 
                        (quote_id, action, status, approver_id, comments, wecom_approval_id, wecom_sp_no, 
                         step_order, is_final_step, created_at) 
                        VALUES 
                        (:quote_id, :action, :status, :approver_id, :comments, :wecom_approval_id, :wecom_sp_no,
                         :step_order, :is_final_step, :created_at)
                    """), {
                        'quote_id': quote.id,
                        'action': new_status,
                        'status': 'completed',
                        'approver_id': None,
                        'comments': '企业微信审批系统自动更新',
                        'wecom_approval_id': sp_no,
                        'wecom_sp_no': sp_no,
                        'step_order': 1,
                        'is_final_step': True,
                        'created_at': datetime.now()
                    })
                except Exception as record_error:
                    print(f"创建审批记录失败: {record_error}")
                    # 审批记录创建失败不影响主要的状态更新
                
                self.db.commit()
                
                # 发送通知给申请人
                if quote.creator and quote.creator.userid:
                    await self.send_approval_notification(
                        quote.id,
                        quote.creator.userid,
                        new_status
                    )
                
                return True
                
        except Exception as e:
            # 记录错误日志（生产环境应使用logging）
            print(f"企业微信回调处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_callback_signature(
        self, 
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echostr: str = None
    ) -> bool:
        """
        验证企业微信回调签名
        
        Args:
            msg_signature: 签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 回显字符串（仅验证URL时使用）
            
        Returns:
            签名是否有效
        """
        token = settings.WECOM_CALLBACK_TOKEN
        
        # 构建签名字符串
        if echostr:
            sign_list = [token, timestamp, nonce, echostr]
        else:
            sign_list = [token, timestamp, nonce]
            
        sign_list.sort()
        sign_str = "".join(sign_list)
        
        # 计算SHA1签名
        calculated_signature = hashlib.sha1(sign_str.encode()).hexdigest()
        
        return calculated_signature == msg_signature
    
    async def sync_approval_status(self, quote_id: int) -> Dict:
        """
        同步报价单的企业微信审批状态
        
        Args:
            quote_id: 报价单ID
            
        Returns:
            同步后的状态信息
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote or not quote.wecom_approval_id:
            return {"status": "no_approval", "message": "无企业微信审批记录"}
        
        # 获取企业微信审批详情
        approval_detail = await self.get_approval_detail(quote.wecom_approval_id)
        
        # 更新本地状态
        sp_status = approval_detail.get("info", {}).get("sp_status")
        status_mapping = {
            1: "pending",
            2: "approved", 
            3: "rejected",
            4: "cancelled"
        }
        
        new_status = status_mapping.get(sp_status, "unknown")
        
        if quote.approval_status != new_status:
            quote.approval_status = new_status
            self.db.commit()
            
        return {
            "status": new_status,
            "wecom_status": sp_status,
            "message": "状态同步成功"
        }