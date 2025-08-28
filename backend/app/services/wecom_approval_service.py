#!/usr/bin/env python3
"""
企业微信审批API集成服务
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import Quote, ApprovalRecord
from ..wecom_auth import WeComOAuth


class WeComApprovalService:
    """企业微信审批服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.wecom = WeComOAuth()
        
        # 企业微信审批相关API
        self.approval_submit_url = "https://qyapi.weixin.qq.com/cgi-bin/oa/applyevent"
        self.approval_detail_url = "https://qyapi.weixin.qq.com/cgi-bin/oa/getapprovalinfo"
        self.approval_template_url = "https://qyapi.weixin.qq.com/cgi-bin/oa/gettemplatedetail"
        
        # 报价单审批模板ID（需要在企业微信管理后台配置）
        self.quote_template_id = os.getenv("WECOM_QUOTE_TEMPLATE_ID", "")
        
    def submit_quote_approval(self, quote_id: int, user_id: int) -> str:
        """
        提交报价单到企业微信审批
        
        Args:
            quote_id: 报价单ID
            user_id: 提交用户ID
            
        Returns:
            企业微信审批单号
        """
        # 获取报价单详情
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")
        
        # 检查报价单状态
        if quote.status != 'draft':
            raise HTTPException(status_code=400, detail="只有草稿状态的报价单可以提交审批")
        
        # 构造审批申请数据
        approval_data = self._build_approval_data(quote, user_id)
        
        try:
            # 调用企业微信API提交审批
            access_token = self.wecom.get_access_token()
            response = requests.post(
                self.approval_submit_url,
                params={"access_token": access_token},
                json=approval_data
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="提交企业微信审批失败")
            
            result = response.json()
            if result.get("errcode", 0) != 0:
                error_msg = result.get("errmsg", "未知错误")
                raise HTTPException(status_code=500, detail=f"企业微信API错误: {error_msg}")
            
            # 获取审批单号
            sp_no = result.get("sp_no")
            if not sp_no:
                raise HTTPException(status_code=500, detail="未获取到审批单号")
            
            # 更新报价单状态和审批单号
            quote.status = 'pending'
            quote.submitted_at = datetime.now()
            quote.wecom_approval_id = sp_no
            
            # 创建审批记录
            approval_record = ApprovalRecord(
                quote_id=quote_id,
                action="submit_wecom_approval",
                status="pending",
                approver_id=user_id,
                comments=f"已提交企业微信审批，审批单号: {sp_no}",
                processed_at=datetime.now()
            )
            self.db.add(approval_record)
            
            self.db.commit()
            return sp_no
            
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"网络请求失败: {str(e)}")
    
    def _build_approval_data(self, quote: Quote, user_id: int) -> Dict[str, Any]:
        """
        构建审批申请数据
        
        Args:
            quote: 报价单对象
            user_id: 申请用户ID
            
        Returns:
            审批申请数据
        """
        # 获取用户信息
        from ..models import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 计算报价明细汇总
        items_summary = []
        if quote.items:
            for item in quote.items:
                items_summary.append(f"{item.item_name}: {item.quantity}{item.unit} × ¥{item.unit_price} = ¥{item.total_price}")
        
        items_text = "\n".join(items_summary) if items_summary else "无明细"
        
        # 构建审批数据
        approval_data = {
            "creator_userid": user.userid,  # 企业微信用户ID
            "template_id": self.quote_template_id,
            "use_template_approver": 0,  # 不使用模板审批人
            "process_code": "",
            "approver": [
                {
                    "attr": 2,  # 指定成员
                    "userid": ["admin"]  # 这里可以配置审批人，暂时使用admin
                }
            ],
            "summary_list": [
                {
                    "summary_info": [
                        {
                            "text": f"报价单号: {quote.quote_number}",
                            "lang": "zh_CN"
                        },
                        {
                            "text": f"客户: {quote.customer_name}",
                            "lang": "zh_CN"
                        },
                        {
                            "text": f"总金额: ¥{quote.total_amount or 0}",
                            "lang": "zh_CN"
                        }
                    ]
                }
            ],
            "apply_data": {
                "contents": [
                    {
                        "control": "Text",
                        "id": "Text-1",
                        "title": [{"text": "报价单号", "lang": "zh_CN"}],
                        "value": {"text": quote.quote_number}
                    },
                    {
                        "control": "Text", 
                        "id": "Text-2",
                        "title": [{"text": "报价标题", "lang": "zh_CN"}],
                        "value": {"text": quote.title}
                    },
                    {
                        "control": "Text",
                        "id": "Text-3", 
                        "title": [{"text": "客户名称", "lang": "zh_CN"}],
                        "value": {"text": quote.customer_name}
                    },
                    {
                        "control": "Text",
                        "id": "Text-4",
                        "title": [{"text": "报价类型", "lang": "zh_CN"}],
                        "value": {"text": self._get_quote_type_display(quote.quote_type)}
                    },
                    {
                        "control": "Money",
                        "id": "Money-1",
                        "title": [{"text": "报价总金额", "lang": "zh_CN"}], 
                        "value": {"new_money": str(int((quote.total_amount or 0) * 100))}  # 分为单位
                    },
                    {
                        "control": "Textarea",
                        "id": "Textarea-1",
                        "title": [{"text": "报价明细", "lang": "zh_CN"}],
                        "value": {"text": items_text}
                    },
                    {
                        "control": "Textarea", 
                        "id": "Textarea-2",
                        "title": [{"text": "备注说明", "lang": "zh_CN"}],
                        "value": {"text": quote.description or "无"}
                    }
                ]
            }
        }
        
        return approval_data
    
    def _get_quote_type_display(self, quote_type: str) -> str:
        """获取报价类型显示名称"""
        type_map = {
            'inquiry': '询价报价',
            'tooling': '工装夹具报价', 
            'engineering': '工程机时报价',
            'mass_production': '量产机时报价',
            'process': '量产工序报价',
            'comprehensive': '综合报价'
        }
        return type_map.get(quote_type, quote_type)
    
    def check_approval_status(self, quote_id: int) -> Dict[str, Any]:
        """
        检查审批状态
        
        Args:
            quote_id: 报价单ID
            
        Returns:
            审批状态信息
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")
        
        if not quote.wecom_approval_id:
            return {"status": "not_submitted", "message": "未提交审批"}
        
        try:
            # 调用企业微信API查询审批状态
            access_token = self.wecom.get_access_token()
            response = requests.post(
                self.approval_detail_url,
                params={"access_token": access_token},
                json={"sp_no": quote.wecom_approval_id}
            )
            
            if response.status_code != 200:
                return {"status": "error", "message": "查询审批状态失败"}
            
            result = response.json()
            if result.get("errcode", 0) != 0:
                return {"status": "error", "message": f"企业微信API错误: {result.get('errmsg')}"}
            
            info = result.get("info", {})
            sp_status = info.get("sp_status", 0)
            
            # 状态映射
            status_map = {
                1: {"status": "pending", "message": "审批中"},
                2: {"status": "approved", "message": "已同意"},
                3: {"status": "rejected", "message": "已驳回"},
                4: {"status": "cancelled", "message": "已撤销"}
            }
            
            status_info = status_map.get(sp_status, {"status": "unknown", "message": "未知状态"})
            
            # 如果状态发生变化，更新本地状态
            if sp_status == 2 and quote.status != 'approved':
                self._update_quote_approval_status(quote, 'approved', "企业微信审批通过")
            elif sp_status == 3 and quote.status != 'rejected':
                rejection_reason = "企业微信审批被拒绝"
                if info.get("comments"):
                    rejection_reason += f": {info.get('comments')}"
                self._update_quote_approval_status(quote, 'rejected', rejection_reason)
            
            return status_info
            
        except requests.RequestException as e:
            return {"status": "error", "message": f"网络请求失败: {str(e)}"}
    
    def _update_quote_approval_status(self, quote: Quote, status: str, comments: str):
        """
        更新报价单审批状态
        
        Args:
            quote: 报价单对象
            status: 新状态
            comments: 备注
        """
        old_status = quote.status
        quote.status = status
        
        if status == 'approved':
            quote.approved_at = datetime.now()
            # 这里可以设置审批人，暂时留空
        elif status == 'rejected':
            quote.rejection_reason = comments
        
        # 创建审批记录
        approval_record = ApprovalRecord(
            quote_id=quote.id,
            action=f"wecom_approval_result:{old_status}->{status}",
            status=status,
            approver_id=None,  # 企业微信审批，暂时不记录具体审批人ID
            comments=comments,
            processed_at=datetime.now()
        )
        self.db.add(approval_record)
        
        self.db.commit()
    
    def get_approval_history(self, quote_id: int) -> Dict[str, Any]:
        """
        获取审批历史记录
        
        Args:
            quote_id: 报价单ID
            
        Returns:
            审批历史记录
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote or not quote.wecom_approval_id:
            return {"records": []}
        
        try:
            # 调用企业微信API获取审批详情
            access_token = self.wecom.get_access_token()
            response = requests.post(
                self.approval_detail_url,
                params={"access_token": access_token},
                json={"sp_no": quote.wecom_approval_id}
            )
            
            if response.status_code != 200:
                return {"records": []}
            
            result = response.json()
            if result.get("errcode", 0) != 0:
                return {"records": []}
            
            info = result.get("info", {})
            records = []
            
            # 解析审批流程记录
            if "sp_record" in info:
                for record in info["sp_record"]:
                    records.append({
                        "approver": record.get("approver", ""),
                        "speech": record.get("speech", ""),
                        "sp_status": record.get("sp_status", 0),
                        "sptime": record.get("sptime", 0),
                        "media_id": record.get("media_id", [])
                    })
            
            return {"records": records}
            
        except requests.RequestException:
            return {"records": []}


class WeComApprovalCallbackHandler:
    """企业微信审批回调处理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.approval_service = WeComApprovalService(db)
    
    def handle_approval_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        处理企业微信审批回调
        
        Args:
            callback_data: 回调数据
            
        Returns:
            处理是否成功
        """
        try:
            # 解析回调数据
            sp_no = callback_data.get("SpNo")
            sp_status = callback_data.get("SpStatus")
            
            if not sp_no:
                return False
            
            # 查找对应的报价单
            quote = self.db.query(Quote).filter(Quote.wecom_approval_id == sp_no).first()
            if not quote:
                return False
            
            # 根据审批结果更新状态
            if sp_status == 2:  # 审批通过
                self.approval_service._update_quote_approval_status(
                    quote, 'approved', "企业微信审批通过"
                )
            elif sp_status == 3:  # 审批拒绝
                comments = callback_data.get("Comments", "企业微信审批被拒绝")
                self.approval_service._update_quote_approval_status(
                    quote, 'rejected', comments
                )
            
            return True
            
        except Exception as e:
            print(f"处理审批回调失败: {e}")
            return False