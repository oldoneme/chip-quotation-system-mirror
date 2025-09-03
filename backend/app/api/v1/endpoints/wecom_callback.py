"""
企业微信回调处理端点
处理企业微信审批系统的回调通知
"""

from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional
import xml.etree.ElementTree as ET
import json
from datetime import datetime

from ....database import get_db
from ....services.wecom_integration import WeComApprovalIntegration
from ....config import settings

router = APIRouter(tags=["企业微信回调"])


@router.get("/verify")
async def verify_callback_url(
    msg_signature: str = Query(..., description="企业微信签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    echostr: str = Query(..., description="回显字符串"),
    db: Session = Depends(get_db)
):
    """
    验证企业微信回调URL
    企业微信配置回调URL时会调用此接口进行验证
    """
    service = WeComApprovalIntegration(db)
    
    # 验证签名
    if not service.verify_callback_signature(msg_signature, timestamp, nonce, echostr):
        raise HTTPException(status_code=403, detail="签名验证失败")
    
    # 验证成功，返回echostr
    return PlainTextResponse(content=echostr)


@router.post("/approval")
async def handle_approval_callback(
    request: Request,
    msg_signature: str = Query(..., description="企业微信签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    db: Session = Depends(get_db)
):
    """
    处理企业微信审批回调
    当审批状态发生变化时，企业微信会调用此接口
    """
    service = WeComApprovalIntegration(db)
    
    # 验证签名
    if not service.verify_callback_signature(msg_signature, timestamp, nonce):
        raise HTTPException(status_code=403, detail="签名验证失败")
    
    # 获取请求体
    body = await request.body()
    
    try:
        # 解析XML数据
        root = ET.fromstring(body)
        
        # 提取关键信息
        msg_type = root.find("MsgType").text if root.find("MsgType") is not None else None
        event = root.find("Event").text if root.find("Event") is not None else None
        
        # 处理审批事件（支持两种事件名称）
        if msg_type == "event" and event in ["open_approval_change", "sys_approval_change"]:
            # 提取审批信息（支持多种字段名）
            approval_info = {
                "ApprovalInfo": {
                    "SpNo": root.find("ApprovalInfo/SpNo").text if root.find("ApprovalInfo/SpNo") is not None else None,
                    "ThirdNo": root.find("ApprovalInfo/ThirdNo").text if root.find("ApprovalInfo/ThirdNo") is not None else None,
                    "SpStatus": int(root.find("ApprovalInfo/SpStatus").text) if root.find("ApprovalInfo/SpStatus") is not None else None,
                    "OpenSpStatus": int(root.find("ApprovalInfo/OpenSpStatus").text) if root.find("ApprovalInfo/OpenSpStatus") is not None else None,
                    "SpName": root.find("ApprovalInfo/SpName").text if root.find("ApprovalInfo/SpName") is not None else None,
                    "ApplyTime": root.find("ApprovalInfo/ApplyTime").text if root.find("ApprovalInfo/ApplyTime") is not None else None,
                }
            }
            
            # 提取EventID用于幂等处理
            event_id = root.find("EventID").text if root.find("EventID") is not None else None
            if event_id:
                approval_info["EventID"] = event_id
            
            # 处理审批回调
            success = await service.handle_approval_callback(approval_info)
            
            if success:
                return PlainTextResponse(content="success")
            else:
                return PlainTextResponse(content="failed")
        
        # 其他事件暂不处理
        return PlainTextResponse(content="success")
        
    except Exception as e:
        print(f"处理回调失败: {str(e)}")
        return PlainTextResponse(content="failed")


@router.post("/message")
async def handle_message_callback(
    request: Request,
    msg_signature: str = Query(..., description="企业微信签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    db: Session = Depends(get_db)
):
    """
    处理企业微信消息回调
    用户在企业微信中发送消息时会调用此接口
    """
    service = WeComApprovalIntegration(db)
    
    # 验证签名
    if not service.verify_callback_signature(msg_signature, timestamp, nonce):
        raise HTTPException(status_code=403, detail="签名验证失败")
    
    # 获取请求体
    body = await request.body()
    
    try:
        # 解析XML数据
        root = ET.fromstring(body)
        
        # 提取消息信息
        msg_type = root.find("MsgType").text if root.find("MsgType") is not None else None
        from_user = root.find("FromUserName").text if root.find("FromUserName") is not None else None
        content = root.find("Content").text if root.find("Content") is not None else None
        
        # 处理文本消息
        if msg_type == "text":
            # 这里可以添加自动回复逻辑
            # 例如：用户发送"审批"关键词，返回待审批列表
            pass
        
        return PlainTextResponse(content="success")
        
    except Exception as e:
        print(f"处理消息失败: {str(e)}")
        return PlainTextResponse(content="failed")


@router.post("/simulate-approval")
async def simulate_approval_callback(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """
    模拟企业微信审批回调 - 用于测试和开发
    
    请求格式:
    {
        "quote_number": "CIS-KS20250902001",
        "action": "approved|rejected|cancelled",
        "sp_no": "审批编号(可选)"
    }
    """
    try:
        quote_number = request_data.get("quote_number")
        action = request_data.get("action")
        sp_no = request_data.get("sp_no")
        
        if not quote_number or not action:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 查找报价单
        from ....models import Quote
        quote = db.query(Quote).filter(Quote.quote_number == quote_number).first()
        
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")
        
        # 如果没有提供sp_no，使用现有的或生成新的
        if not sp_no:
            sp_no = quote.wecom_approval_id or f"sim_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 确保报价单有企业微信审批ID
        if not quote.wecom_approval_id:
            quote.wecom_approval_id = sp_no
            db.commit()
        
        # 映射操作到企业微信状态码
        action_mapping = {
            "approved": 2,
            "rejected": 3,
            "cancelled": 4
        }
        
        sp_status = action_mapping.get(action)
        if not sp_status:
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        # 构建回调数据
        callback_data = {
            "ApprovalInfo": {
                "SpNo": sp_no,
                "SpStatus": sp_status,
                "SpName": f"报价单{quote_number}审批",
                "ApplyTime": int(datetime.now().timestamp())
            }
        }
        
        # 处理回调
        service = WeComApprovalIntegration(db)
        success = await service.handle_approval_callback(callback_data)
        
        if success:
            # 刷新报价单数据
            db.refresh(quote)
            return {
                "success": True,
                "message": f"模拟回调处理成功",
                "quote": {
                    "quote_number": quote.quote_number,
                    "status": quote.status,
                    "approval_status": quote.approval_status,
                    "updated_at": quote.updated_at.isoformat()
                }
            }
        else:
            return {
                "success": False,
                "message": "回调处理失败"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"模拟回调处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
        
        
@router.post("/sync-approval-status")
async def sync_approval_status(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """
    主动同步企业微信审批状态
    可以同步单个报价单或所有待审批的报价单
    
    请求格式:
    {
        "quote_number": "报价单号(可选，不提供则同步所有pending状态)",
        "force": false  # 是否强制同步，即使不是pending状态
    }
    """
    try:
        from ....services.wecom_approval_sync import WeComApprovalSyncService
        
        sync_service = WeComApprovalSyncService()
        quote_number = request_data.get("quote_number")
        force_sync = request_data.get("force", False)
        
        if quote_number:
            # 同步指定报价单
            from ....models import Quote
            quote = db.query(Quote).filter(Quote.quote_number == quote_number).first()
            
            if not quote:
                raise HTTPException(status_code=404, detail="报价单不存在")
            
            # 检查是否需要同步
            if not force_sync and quote.status not in ['pending']:
                return {
                    "success": True,
                    "message": f"报价单 {quote_number} 状态为 {quote.status}，无需同步",
                    "quote": {
                        "quote_number": quote.quote_number,
                        "status": quote.status,
                        "approval_status": quote.approval_status
                    }
                }
            
            # 执行同步
            success = await sync_service.sync_approval_status(quote.id)
            
            # 刷新报价单数据
            db.refresh(quote)
            
            return {
                "success": success,
                "message": f"{'成功' if success else '失败'}同步报价单 {quote_number}",
                "quote": {
                    "quote_number": quote.quote_number,
                    "status": quote.status,
                    "approval_status": quote.approval_status,
                    "updated_at": quote.updated_at.isoformat()
                }
            }
        else:
            # 同步所有待审批的报价单
            result = await sync_service.sync_all_pending_quotes()
            
            return {
                "success": True,
                "message": f"批量同步完成",
                "result": result
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"同步审批状态异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
    finally:
        if 'sync_service' in locals():
            sync_service.close()


@router.get("/test-endpoints")
async def list_test_endpoints():
    """
    列出所有测试相关的端点
    """
    return {
        "endpoints": [
            {
                "path": "/api/v1/wecom-callback/simulate-approval",
                "method": "POST",
                "description": "模拟企业微信审批回调",
                "example": {
                    "quote_number": "CIS-KS20250902001",
                    "action": "approved|rejected|cancelled",
                    "sp_no": "可选的审批编号"
                }
            },
            {
                "path": "/api/v1/wecom-callback/sync-approval-status",
                "method": "POST",
                "description": "主动同步企业微信审批状态",
                "example": {
                    "quote_number": "可选，不提供则同步所有",
                    "force": false
                }
            },
            {
                "path": "/api/v1/wecom-callback/verify",
                "method": "GET",
                "description": "验证企业微信回调URL",
                "params": "msg_signature, timestamp, nonce, echostr"
            },
            {
                "path": "/api/v1/wecom-callback/approval",
                "method": "POST", 
                "description": "真实的企业微信审批回调处理",
                "params": "msg_signature, timestamp, nonce + XML body"
            }
        ]
    }