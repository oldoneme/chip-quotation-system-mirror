"""
企业微信审批集成服务
处理企业微信审批流程的核心功能
"""

import json
import time
import hashlib
import secrets
import os
import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Quote, ApprovalRecord, User
from ..database import get_db
from ..config import settings
from .quote_service import QuoteService


class WeComApprovalIntegration:
    """企业微信审批集成服务"""
    
    # 重试配置
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # 基础延迟时间(秒)
    MAX_DELAY = 10.0  # 最大延迟时间(秒)
    TIMEOUT = 30.0    # 请求超时时间(秒)
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.corp_id = settings.WECOM_CORP_ID
        self.agent_id = settings.WECOM_AGENT_ID
        self.secret = settings.WECOM_SECRET
        self.approval_template_id = settings.WECOM_APPROVAL_TEMPLATE_ID
        self.callback_url = settings.WECOM_CALLBACK_URL.rstrip('/')
        self.base_url = settings.WECOM_BASE_URL.rstrip('/')
        self.callback_token = settings.WECOM_CALLBACK_TOKEN
        self.encoding_aes_key = settings.WECOM_ENCODING_AES_KEY
        self._access_token = None
        self._token_expires_at = None
        
        # 设置环境变量避免代理干扰企业微信API调用
        os.environ['NO_PROXY'] = 'qyapi.weixin.qq.com,*.weixin.qq.com'
        # 强制清空所有代理环境变量避免httpx检测到无效代理
        for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
            if proxy_var in os.environ:
                del os.environ[proxy_var]
    
    async def _retry_request(self, method: str, url: str, **kwargs) -> Dict:
        """
        带重试机制的HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, etc.)
            url: 请求URL
            **kwargs: httpx请求参数
            
        Returns:
            响应的JSON数据
            
        Raises:
            HTTPException: 重试耗尽后仍然失败
        """
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                timeout = httpx.Timeout(self.TIMEOUT)
                async with httpx.AsyncClient(proxy=None, timeout=timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, **kwargs)
                    elif method.upper() == "POST":
                        response = await client.post(url, **kwargs)
                    else:
                        raise ValueError(f"不支持的HTTP方法: {method}")
                    
                    # 检查HTTP状态码
                    response.raise_for_status()
                    return response.json()
                    
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError) as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    # 指数退避延迟
                    delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)
                    print(f"⚠️ 网络请求失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {str(e)}")
                    print(f"   等待 {delay:.1f}秒 后重试...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    print(f"❌ 网络请求重试耗尽，最终失败: {str(e)}")
                    break
                    
            except httpx.HTTPStatusError as e:
                # HTTP状态码错误不重试，直接返回
                print(f"❌ HTTP状态错误: {e.response.status_code}")
                return e.response.json()
                
            except Exception as e:
                last_exception = e
                print(f"❌ 未知错误: {str(e)}")
                break
        
        # 重试耗尽，抛出异常
        raise HTTPException(
            status_code=500,
            detail=f"网络请求失败，已重试{self.MAX_RETRIES}次: {str(last_exception)}"
        )
        
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
        
        data = await self._retry_request("GET", url, params=params)
            
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
        
        result = await self._retry_request("POST", url, files=files)
            
        if result.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {result.get('errmsg')}"
            )
            
        return result["media_id"]

    async def upload_file_path(self, file_path: str, mime_type: str = "application/pdf") -> Optional[str]:
        """上传本地文件到企业微信，返回 media_id"""
        if not file_path or not os.path.exists(file_path):
            return None

        access_token = await self.get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=file"

        try:
            with open(file_path, "rb") as f:
                files = {
                    'media': (os.path.basename(file_path), f, mime_type)
                }
                result = await self._retry_request("POST", url, files=files)
        except Exception as exc:
            self.logger.error(f"上传文件失败 {file_path}: {exc}")
            return None

        if result.get("errcode") != 0:
            self.logger.error(f"企业微信文件上传失败: {result}")
            return None

        return result.get("media_id")
    
    async def submit_quote_approval(self, quote_id, approver_userid: str = None, creator_userid: str = None) -> Dict:
        """
        提交报价单到企业微信审批
        使用模板定义的审批人，简化流程
        
        Args:
            quote_id: 报价单ID
            approver_userid: 可选的审批人ID（如果不使用模板审批人）
            
        Returns:
            审批申请创建结果
        """
        # 查询报价单（现在只支持整数ID）
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")
        
        access_token = await self.get_access_token()
        
        # 生成报价单详情的审批链接
        # 优先使用UUID token，回退到数字ID
        if hasattr(quote, 'approval_link_token') and quote.approval_link_token:
            # 使用UUID token生成前端链接
            detail_link = f"{settings.WECOM_BASE_URL}/quote-detail/{quote.approval_link_token}"
        else:
            # 回退到旧的OAuth认证方式
            oauth_redirect_url = f"{settings.API_BASE_URL}/v1/auth/callback"
            detail_state = f"quote_detail_{quote.id}"
            from urllib.parse import quote as url_quote
            detail_link = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={self.corp_id}&redirect_uri={url_quote(oauth_redirect_url, safe='')}&response_type=code&scope=snsapi_base&state={detail_state}&agentid={self.agent_id}#wechat_redirect"
        
        # 构建简洁的描述信息（由于Text字段长度限制）
        total_amount = quote.total_amount or 0.0
        description_with_link = f"{quote.description or ''}。💰总金额¥{total_amount:.2f}。📋详情链接见附件"
        
        # 创建简洁的链接文件
        link_file_content = f"报价单详情链接：\n{detail_link}\n\n点击上方链接查看详情"
        media_id = await self.upload_temp_file(link_file_content, f"{quote.quote_number}_链接.txt")
        
        # 构建审批申请数据 - 使用真实的模板字段ID
        # 如果没有传入creator_userid，尝试从报价单获取，但避免使用lazy-loaded关系
        if not creator_userid:
            # 直接查询创建者，避免lazy-loaded关系
            from ..models import User
            creator = self.db.query(User).filter(User.id == quote.created_by).first()
            creator_userid = creator.userid if creator and hasattr(creator, 'userid') else ""
        approval_data = {
            "creator_userid": creator_userid,
            "template_id": self.approval_template_id,
            "use_template_approver": 1,  # 使用模板中定义的审批人
            "third_no": str(quote.id),  # 添加第三方单号用于回调映射
            "apply_data": {
                "contents": [
                    {"control": "Text", "id": "Text-1756706105289", "value": {"text": quote.quote_type or "标准报价"}},
                    {"control": "Text", "id": "Text-1756705975378", "value": {"text": quote.quote_number}},
                    {"control": "Text", "id": "Text-1756706001498", "value": {"text": quote.customer_name}},
                    {"control": "Text", "id": "Text-1756706160253", "value": {"text": description_with_link}},
                    {"control": "Text", "id": "Text-1756897248857", "value": {"text": detail_link}},
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
        
        result = await self._retry_request("POST", url, json=approval_data)
            
        if result.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"提交审批失败: {result.get('errmsg', 'Unknown error')}"
            )
        
        # 保存审批ID到报价单
        quote.wecom_approval_id = result["sp_no"]
        quote.status = "pending"
        quote.approval_status = "pending"
        quote.approval_method = "wecom"
        quote.submitted_at = datetime.utcnow()
        
        # 先提交SQLAlchemy的更改
        self.db.commit()
        
        # 保存审批实例映射（用于回调时查找）- 在SQLAlchemy提交后进行
        import sqlite3
        from sqlalchemy.engine.url import make_url

        db_url = make_url(settings.DATABASE_URL)
        db_path = db_url.database if db_url.drivername.startswith('sqlite') else None
        if db_path and not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)

        if not db_path:
            raise HTTPException(status_code=500, detail="仅支持SQLite数据库的审批实例映射存储")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO approval_instance 
                (quotation_id, sp_no, third_no, status) 
                VALUES (?, ?, ?, ?)
            """, (quote.id, result["sp_no"], str(quote.id), "pending"))
            conn.commit()
        finally:
            conn.close()
        
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
        
        result = await self._retry_request("POST", url, json=data)
            
        if result.get("errcode") != 0:
            raise HTTPException(
                status_code=500,
                detail=f"获取审批详情失败: {result.get('errmsg')}"
            )
        
        return result
    
    async def send_approval_notification(
        self, 
        quote_id, 
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
        # 查询报价单（现在只支持整数ID）
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            
        if not quote:
            return False
        
        access_token = await self.get_access_token()
        
        # 生成审批链接，优先使用UUID token
        if hasattr(quote, 'approval_link_token') and quote.approval_link_token:
            # 使用UUID token生成前端链接
            approval_url = f"{settings.WECOM_BASE_URL}/quote-detail/{quote.approval_link_token}"
        else:
            # 回退到旧的OAuth认证方式
            from urllib.parse import quote as url_quote
            app_url = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={self.corp_id}&redirect_uri={url_quote(f'{settings.API_BASE_URL}/v1/auth/callback', safe='')}&response_type=code&scope=snsapi_base&state=quote_detail_{quote_id}&agentid={self.agent_id}#wechat_redirect"
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

        result = await self._retry_request("POST", url, json=message_data)

        success = result.get("errcode") == 0

        # 如果存在PDF缓存，追加发送文件消息
        pdf_media_id = None
        try:
            acting_user = None
            if quote.created_by:
                acting_user = self.db.query(User).filter(User.id == quote.created_by).first()

            if acting_user is None:
                acting_user = (
                    self.db.query(User)
                    .filter(User.role.in_(['admin', 'super_admin']))
                    .order_by(User.id.asc())
                    .first()
                )

            if acting_user:
                try:
                    QuoteService(self.db).ensure_pdf_cache(quote, acting_user)
                except Exception as ensure_exc:
                    self.logger.error(f"确保PDF缓存失败: {ensure_exc}")

            self.db.refresh(quote)
            pdf_path = None
            cache = getattr(quote, 'pdf_cache', None)
            if cache and cache.pdf_path:
                pdf_path = cache.pdf_path

            if pdf_path:
                if not os.path.isabs(pdf_path):
                    pdf_path = os.path.join(os.getcwd(), pdf_path)
                if os.path.exists(pdf_path):
                    self.logger.info(f"上传报价单PDF附件: {pdf_path}")
                    pdf_media_id = await self.upload_file_path(pdf_path)
                else:
                    self.logger.warning(f"报价单PDF文件不存在: {pdf_path}")
            else:
                self.logger.info("未找到报价单PDF缓存，跳过附件发送")

            if pdf_media_id:
                file_message = {
                    "touser": approver_userid,
                    "msgtype": "file",
                    "agentid": self.agent_id,
                    "file": {"media_id": pdf_media_id}
                }
                await self._retry_request("POST", url, json=file_message)
        except Exception as exc:
            self.logger.error(f"发送PDF附件失败: {exc}")

        return success
    
    async def handle_approval_callback(self, callback_data: Dict) -> bool:
        """
        处理企业微信审批回调
        现在通过统一审批引擎处理，确保数据一致性

        Args:
            callback_data: 回调数据

        Returns:
            处理是否成功
        """
        try:
            # 解析回调数据
            sp_status = callback_data.get("ApprovalInfo", {}).get("SpStatus")
            sp_no = callback_data.get("ApprovalInfo", {}).get("SpNo")
            approver_info = callback_data.get("ApprovalInfo", {}).get("Approver", {})

            if not sp_no:
                return False

            # 状态映射
            status_mapping = {
                1: "pending",     # 审批中
                2: "approved",    # 已通过
                3: "rejected",    # 已拒绝
                4: "cancelled"    # 已撤销
            }

            new_status = status_mapping.get(sp_status)
            if not new_status:
                return False

            # 使用统一审批引擎处理状态同步
            from .approval_engine import UnifiedApprovalEngine
            approval_engine = UnifiedApprovalEngine(self.db)

            success = await approval_engine.sync_from_wecom_status_change(
                sp_no=sp_no,
                new_status=new_status,
                operator_info=approver_info
            )

            return success

        except Exception as e:
            # 使用统一的日志系统
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"企业微信回调处理异常: {str(e)}")
            return False
    
    def verify_callback_signature(
        self, 
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echostr: str = None,
        encrypted_msg: str = None
    ) -> bool:
        """
        验证企业微信回调签名
        
        Args:
            msg_signature: 签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 回显字符串（仅验证URL时使用）
            encrypted_msg: 加密消息（POST回调时使用）
            
        Returns:
            签名是否有效
        """
        from ..utils.wecom_crypto import wecom_signature
        
        token = settings.WECOM_CALLBACK_TOKEN
        
        if not token:
            print(f"❌ WECOM_CALLBACK_TOKEN 未配置")
            return False
        
        # 确定第四个参数
        fourth = echostr or encrypted_msg
        if not fourth:
            print(f"❌ 缺少签名参数：echostr 或 encrypted_msg")
            return False
        
        # 计算签名
        calculated_signature = wecom_signature(token, timestamp, nonce, fourth)
        
        # 验证签名
        is_valid = calculated_signature == msg_signature
        
        # 审计日志（脱敏）
        print(f"🔍 企业微信回调签名验证:")
        print(f"   msg_signature: {msg_signature}")
        print(f"   timestamp: {timestamp}")
        print(f"   nonce: {nonce}")
        print(f"   fourth(len): {len(echostr or encrypted_msg or '') if (echostr or encrypted_msg) else 'None'}")
        print(f"   calculated: {calculated_signature}")
        print(f"   result: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        # 严禁开发模式跳过验证
        return is_valid
    
    async def sync_approval_status(self, quote_id) -> Dict:
        """
        同步报价单的企业微信审批状态
        
        Args:
            quote_id: 报价单ID
            
        Returns:
            同步后的状态信息
        """
        # 查询报价单（现在只支持整数ID）
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
        
        if quote.approval_status != new_status or quote.status != new_status:
            quote.approval_status = new_status
            status_mapping_back = {
                "pending": "pending",
                "approved": "approved",
                "rejected": "rejected",
                "cancelled": "cancelled",
            }
            quote.status = status_mapping_back.get(new_status, quote.status)
            self.db.commit()
            
        return {
            "status": new_status,
            "wecom_status": sp_status,
            "message": "状态同步成功"
        }

    async def send_approval_status_update_notification(self, quote_id: int, action: str, operator_name: str = None, comments: str = None) -> Dict:
        """
        发送审批状态更新通知
        当在内部应用中操作审批后，发送详细的状态更新通知

        Args:
            quote_id: 报价单ID
            action: 操作类型 (approve, reject, withdraw等)
            operator_name: 操作人姓名
            comments: 操作备注

        Returns:
            通知发送结果
        """
        try:
            # 查询报价单
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                return {"success": False, "message": "报价单不存在"}

            # 获取创建者信息
            from ..models import User
            creator = self.db.query(User).filter(User.id == quote.created_by).first()
            creator_userid = creator.userid if creator and hasattr(creator, 'userid') else None

            if not creator_userid:
                return {"success": False, "message": "找不到创建者企业微信ID"}

            # 构建状态更新通知消息
            action_text = {
                'approve': '✅ 已批准',
                'reject': '❌ 已拒绝',
                'withdraw': '🔄 已撤回',
                'submit': '📋 已提交'
            }.get(action, f'📝 {action}')

            # 检查是否有企业微信审批ID
            wecom_info = ""
            if quote.wecom_approval_id:
                wecom_info = f"\n📱 企业微信审批单: {quote.wecom_approval_id}"

            # 构建详细的状态更新消息
            detail_link = f"{self.base_url}/quote-detail/{quote.quote_number}"

            title = f"🔔 审批状态更新通知"
            content = f"""
报价单号: {quote.quote_number}
项目名称: {quote.title or '无'}
客户名称: {quote.customer_name or '无'}

{action_text}
操作人: {operator_name or '系统'}
操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            if comments:
                content += f"\n备注: {comments}"

            content += f"{wecom_info}"
            content += f"\n\n💻 查看详情: {detail_link}"

            # 如果有企业微信审批ID，提醒用户关于审批状态
            if quote.wecom_approval_id:
                content += f"\n\n⚠️ 注意: 此操作在内部应用完成，企业微信审批通知中的状态不会自动更新。如需在企业微信中记录，请手动处理相应的审批单。"

            # 发送企业微信消息
            message_data = {
                "touser": creator_userid,
                "msgtype": "textcard",
                "agentid": self.agent_id,
                "textcard": {
                    "title": title,
                    "description": content,
                    "url": detail_link,
                    "btntxt": "查看详情"
                }
            }

            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"

            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(url, json=message_data)
                result = response.json()

                if result.get("errcode") == 0:
                    return {"success": True, "message": "状态更新通知已发送"}
                else:
                    return {"success": False, "message": f"发送失败: {result.get('errmsg', '未知错误')}"}

        except Exception as e:
            return {"success": False, "message": f"发送通知失败: {str(e)}"}

    async def send_status_clarification_message(self, quote_id: int, internal_action: str, recipient_userid: str = None) -> Dict:
        """
        发送状态澄清消息，解决企业微信状态与内部系统不一致的困惑

        当内部系统已经批准/拒绝报价单，但企业微信回调试图修改状态时，
        发送澄清消息告知用户以内部系统状态为准

        Args:
            quote_id: 报价单ID
            internal_action: 内部系统的操作 ("approve" 或 "reject")
            recipient_userid: 接收者企业微信ID，None时发送给创建者

        Returns:
            发送结果
        """
        try:
            # 查询报价单
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                return {"success": False, "message": "报价单不存在"}

            # 获取接收者信息
            if not recipient_userid:
                # 默认发送给创建者
                from ..models import User
                creator = self.db.query(User).filter(User.id == quote.created_by).first()
                recipient_userid = creator.userid if creator and hasattr(creator, 'userid') else None

            if not recipient_userid:
                return {"success": False, "message": "找不到接收者企业微信ID"}

            # 构建澄清消息
            action_text = {
                'approve': '✅ 已批准',
                'reject': '❌ 已拒绝'
            }.get(internal_action, internal_action)

            title = "🔧 审批状态澄清通知"

            # 检查是否存在企业微信审批ID
            wecom_info = ""
            if quote.wecom_approval_id:
                wecom_info = f"企业微信审批单: {quote.wecom_approval_id}\n"

            content = f"""
{wecom_info}报价单号: {quote.quote_number}
项目名称: {quote.title or '无'}

🎯 重要提醒:
此报价单在内部系统中的状态为: {action_text}

⚠️ 状态说明:
如果您在企业微信审批通知中看到不同的状态显示，请以此内部系统状态为准。企业微信中的状态显示可能存在延迟或不同步的情况。

📋 审批流程说明:
• 内部系统状态是最终有效状态
• 企业微信通知仅作为流程辅助工具
• 如有疑问，请咨询管理员

💻 查看准确状态: {self.base_url}/quote-detail/{quote.quote_number}"""

            # 发送企业微信消息
            message_data = {
                "touser": recipient_userid,
                "msgtype": "textcard",
                "agentid": self.agent_id,
                "textcard": {
                    "title": title,
                    "description": content,
                    "url": f"{self.base_url}/quote-detail/{quote.quote_number}",
                    "btntxt": "查看详情"
                }
            }

            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"

            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(url, json=message_data)
                result = response.json()

                if result.get("errcode") == 0:
                    return {"success": True, "message": "状态澄清消息已发送"}
                else:
                    return {"success": False, "message": f"发送失败: {result.get('errmsg', '未知错误')}"}

        except Exception as e:
            return {"success": False, "message": f"发送澄清消息失败: {str(e)}"}

    async def investigate_approval_delegation_api(self, quote_id: int) -> Dict:
        """
        探索企业微信审批代理功能
        查看是否可以通过设置代理人的方式实现状态同步
        """
        # 注意：这是一个实验性方法，用于探索可能的API
        try:
            # 1. 查看是否有设置审批代理的API
            # 2. 或者是否可以以代理人身份操作审批

            # 这需要进一步研究企业微信的代理审批API
            # 可能的API端点：
            # - /cgi-bin/oa/approval/delegate  (假设)
            # - /cgi-bin/oa/approval/operate   (假设)

            return {
                "success": False,
                "message": "代理审批功能需要进一步研究企业微信API文档",
                "suggestions": [
                    "联系企业微信技术支持了解代理审批API",
                    "查看企业微信管理后台是否有代理设置功能",
                    "考虑使用webhook方式实现状态同步"
                ]
            }

        except Exception as e:
            return {"success": False, "message": f"探索代理功能失败: {str(e)}"}
