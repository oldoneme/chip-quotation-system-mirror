#!/usr/bin/env python3
"""
企业微信运维工具端点
提供健康检查、补偿任务、密钥巡检等运维功能
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
import json

from ....database import get_db
from ....models import Quote, ApprovalTimeline, ApprovalTimelineErrors
from ....config import settings
from ....services.wecom_compensation import WeComCompensationService

router = APIRouter(tags=["企业微信运维"])


@router.get("/internal/health")
async def health_check(db: Session = Depends(get_db)):
    """
    健康页：返回最近5条approval_timeline与处理耗时
    """
    try:
        # 最近5条审批时间线
        recent_timelines = db.query(ApprovalTimeline)\
            .order_by(ApprovalTimeline.created_at.desc())\
            .limit(5).all()
        
        timelines_data = []
        for timeline in recent_timelines:
            timelines_data.append({
                "event_id": timeline.event_id[:12] + "..." if timeline.event_id and len(timeline.event_id) > 12 else timeline.event_id,
                "sp_no": timeline.sp_no,
                "third_no": timeline.third_no,
                "status": timeline.status,
                "created_at": timeline.created_at.isoformat(),
                "age_minutes": int((datetime.now() - timeline.created_at).total_seconds() / 60)
            })
        
        # 系统状态统计
        total_quotes = db.query(Quote).count()
        pending_quotes = db.query(Quote).filter(Quote.status == "pending").count()
        
        # 超时pending统计（超过10分钟）
        cutoff_time = datetime.now() - timedelta(minutes=10)
        stuck_quotes = db.query(Quote).filter(
            Quote.status == "pending",
            Quote.wecom_approval_id.isnot(None),
            Quote.updated_at < cutoff_time
        ).count()
        
        # 错误统计
        error_count_24h = db.query(ApprovalTimelineErrors)\
            .filter(ApprovalTimelineErrors.created_at > datetime.now() - timedelta(hours=24))\
            .count()
        
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "healthy" if stuck_quotes == 0 else "warning",
            "statistics": {
                "total_quotes": total_quotes,
                "pending_quotes": pending_quotes,
                "stuck_quotes": stuck_quotes,
                "errors_24h": error_count_24h
            },
            "recent_timelines": timelines_data,
            "config_status": {
                "wecom_token_configured": bool(settings.WECOM_CALLBACK_TOKEN),
                "wecom_aes_key_configured": bool(settings.WECOM_ENCODING_AES_KEY),
                "wecom_aes_key_length": len(settings.WECOM_ENCODING_AES_KEY) if settings.WECOM_ENCODING_AES_KEY else 0,
                "corp_id_configured": bool(settings.WECOM_CORP_ID)
            }
        }
        
        return health_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.post("/internal/reconcile")  
async def trigger_reconciliation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    跑批按钮：管理页一键触发"对账补偿"
    """
    async def run_reconciliation():
        try:
            print("🚀 开始执行对账补偿任务")
            sync_service = WeComCompensationService()
            result = await sync_service.sync_all_pending_quotes()
            print(f"✅ 对账补偿任务完成: {result}")
            sync_service.close()
        except Exception as e:
            print(f"❌ 对账补偿任务异常: {str(e)}")
    
    # 后台执行补偿任务
    background_tasks.add_task(run_reconciliation)
    
    return {
        "message": "对账补偿任务已启动",
        "started_at": datetime.now().isoformat(),
        "note": "任务在后台执行，可通过健康检查端点查看结果"
    }


@router.get("/internal/config-check")
async def config_check():
    """
    密钥巡检：每天0点校验AESKey=43位、Token非空、应用端"保存并测试"通
    """
    checks = []
    overall_status = "pass"
    
    # 检查Token
    token_ok = bool(settings.WECOM_CALLBACK_TOKEN)
    checks.append({
        "item": "WECOM_CALLBACK_TOKEN",
        "status": "pass" if token_ok else "fail",
        "message": "已配置" if token_ok else "未配置或为空"
    })
    if not token_ok:
        overall_status = "fail"
    
    # 检查AES Key
    aes_key = settings.WECOM_ENCODING_AES_KEY
    aes_key_ok = aes_key and len(aes_key) == 43
    checks.append({
        "item": "WECOM_ENCODING_AES_KEY",
        "status": "pass" if aes_key_ok else "fail", 
        "message": f"长度{len(aes_key)}位" if aes_key else "未配置",
        "expected": "43位"
    })
    if not aes_key_ok:
        overall_status = "fail"
    
    # 检查Corp ID
    corp_id_ok = bool(settings.WECOM_CORP_ID)
    checks.append({
        "item": "WECOM_CORP_ID",
        "status": "pass" if corp_id_ok else "fail",
        "message": "已配置" if corp_id_ok else "未配置或为空"
    })
    if not corp_id_ok:
        overall_status = "fail"
    
    return {
        "timestamp": datetime.now().isoformat(),
        "overall_status": overall_status,
        "checks": checks,
        "next_check": (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
    }


@router.get("/internal/errors")
async def get_recent_errors(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取最近的错误记录
    """
    try:
        errors = db.query(ApprovalTimelineErrors)\
            .order_by(ApprovalTimelineErrors.created_at.desc())\
            .limit(limit).all()
        
        error_data = []
        for error in errors:
            error_data.append({
                "id": error.id,
                "event_id": error.event_id,
                "sp_no": error.sp_no,
                "third_no": error.third_no,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "created_at": error.created_at.isoformat(),
                "age_minutes": int((datetime.now() - error.created_at).total_seconds() / 60)
            })
        
        return {
            "total": len(error_data),
            "errors": error_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误记录失败: {str(e)}")


@router.get("/internal/quotes-status")
async def get_quotes_status(db: Session = Depends(get_db)):
    """
    获取报价单状态分布
    """
    try:
        from sqlalchemy import func
        
        # 按状态统计报价单数量
        status_counts = db.query(
            Quote.status,
            func.count(Quote.id).label('count')
        ).group_by(Quote.status).all()
        
        status_distribution = {}
        total = 0
        for status, count in status_counts:
            status_distribution[status] = count
            total += count
        
        # 查找超时的pending报价单
        cutoff_time = datetime.now() - timedelta(minutes=10)
        stuck_quotes_query = db.query(Quote).filter(
            Quote.status == "pending",
            Quote.wecom_approval_id.isnot(None),
            Quote.updated_at < cutoff_time
        )
        
        stuck_quotes = []
        for quote in stuck_quotes_query.limit(10).all():
            stuck_quotes.append({
                "id": quote.id,
                "quote_number": quote.quote_number,
                "status": quote.status,
                "wecom_approval_id": quote.wecom_approval_id,
                "updated_at": quote.updated_at.isoformat(),
                "stuck_minutes": int((datetime.now() - quote.updated_at).total_seconds() / 60)
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_quotes": total,
            "status_distribution": status_distribution,
            "stuck_quotes_count": stuck_quotes_query.count(),
            "stuck_quotes_sample": stuck_quotes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报价单状态失败: {str(e)}")


@router.post("/internal/test-callback")
async def test_callback_system():
    """
    测试回调系统是否正常工作
    """
    try:
        # 这里可以添加回调系统的基本测试
        # 比如验证签名算法、AES解密等
        
        from ....utils.wecom_crypto import wecom_signature, aes_key_iv
        
        # 测试签名算法
        test_signature = wecom_signature(
            settings.WECOM_CALLBACK_TOKEN,
            "1234567890", 
            "test_nonce",
            "test_fourth"
        )
        
        # 测试AES密钥生成
        try:
            key, iv = aes_key_iv(settings.WECOM_ENCODING_AES_KEY)
            aes_test_ok = len(key) == 32 and len(iv) == 16
        except Exception:
            aes_test_ok = False
        
        return {
            "timestamp": datetime.now().isoformat(),
            "tests": [
                {
                    "test": "签名算法",
                    "status": "pass" if test_signature else "fail",
                    "result": test_signature[:16] + "..." if test_signature else "None"
                },
                {
                    "test": "AES密钥生成",
                    "status": "pass" if aes_test_ok else "fail",
                    "result": f"key={len(key)}字节, iv={len(iv)}字节" if aes_test_ok else "失败"
                }
            ],
            "overall_status": "pass" if (test_signature and aes_test_ok) else "fail"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试回调系统失败: {str(e)}")


@router.get("/internal/ops-summary")
async def ops_summary():
    """
    运维小抄：汇总所有运维信息
    """
    return {
        "endpoints": [
            {
                "path": "/internal/health",
                "method": "GET", 
                "description": "健康页：最近5条approval_timeline与处理耗时"
            },
            {
                "path": "/internal/reconcile",
                "method": "POST",
                "description": "跑批按钮：一键触发对账补偿"
            },
            {
                "path": "/internal/config-check", 
                "method": "GET",
                "description": "密钥巡检：校验AESKey=43位、Token非空"
            },
            {
                "path": "/internal/errors",
                "method": "GET",
                "description": "获取最近的错误记录"
            },
            {
                "path": "/internal/quotes-status",
                "method": "GET",
                "description": "获取报价单状态分布和卡住的报价单"
            },
            {
                "path": "/internal/test-callback",
                "method": "POST",
                "description": "测试回调系统是否正常工作"
            }
        ],
        "scheduled_tasks": [
            {
                "task": "对账补偿",
                "frequency": "每2分钟",
                "description": "扫描pending超过10分钟的报价单进行补偿"
            },
            {
                "task": "密钥巡检", 
                "frequency": "每天0点",
                "description": "校验AESKey、Token配置正确性"
            }
        ],
        "alert_conditions": [
            {
                "condition": "pending超过10分钟",
                "action": "发钉/企微机器人提醒 + 触发补偿任务"
            },
            {
                "condition": "错误留痕表新增记录",
                "action": "记录异常事件避免日志滚动丢线索"
            }
        ]
    }