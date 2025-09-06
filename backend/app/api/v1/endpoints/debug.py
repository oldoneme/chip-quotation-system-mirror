#!/usr/bin/env python3
"""
调试端点 - 用于诊断报价单和审批状态同步问题
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from typing import Dict, Any, Optional

from ....database import get_db
from ....models import Quote, ApprovalTimeline, ApprovalTimelineErrors

router = APIRouter(tags=["调试"])


@router.get("/internal/debug/quote/{quote_id}")
async def debug_quote_status(quote_id: int, db: Session = Depends(get_db)):
    """
    调试报价单状态和审批事件
    """
    try:
        # 获取报价单信息
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")
        
        # 获取最新的审批时间线
        latest_timeline = db.query(ApprovalTimeline)\
            .filter(ApprovalTimeline.third_no == str(quote_id))\
            .order_by(ApprovalTimeline.created_at.desc())\
            .first()
        
        # 获取所有相关的审批时间线
        all_timelines = db.query(ApprovalTimeline)\
            .filter(ApprovalTimeline.third_no == str(quote_id))\
            .order_by(ApprovalTimeline.created_at.desc())\
            .all()
        
        # 获取错误记录
        errors = db.query(ApprovalTimelineErrors)\
            .filter(ApprovalTimelineErrors.third_no == str(quote_id))\
            .order_by(ApprovalTimelineErrors.created_at.desc())\
            .all()
        
        # 构建响应
        result = {
            "quotation_info": {
                "id": quote.id,
                "quote_number": quote.quote_number,
                "status": quote.status,
                "approval_status": quote.approval_status,
                "wecom_approval_id": quote.wecom_approval_id,
                "last_updated": quote.updated_at.isoformat() if quote.updated_at else None,
                "created_at": quote.created_at.isoformat() if quote.created_at else None
            },
            "latest_event": None,
            "all_events": [],
            "errors": [],
            "system_info": {
                "db_path": os.path.abspath("app/test.db"),
                "process_id": os.getpid(),
                "instance_id": f"backend-{os.getpid()}"
            }
        }
        
        if latest_timeline:
            result["latest_event"] = {
                "event_id": latest_timeline.event_id,
                "sp_no": latest_timeline.sp_no,
                "third_no": latest_timeline.third_no,
                "status": latest_timeline.status,
                "created_at": latest_timeline.created_at.isoformat(),
                "status_text": {
                    1: "pending",
                    2: "approved", 
                    3: "rejected",
                    4: "cancelled"
                }.get(latest_timeline.status, f"unknown({latest_timeline.status})")
            }
        
        # 所有事件
        for timeline in all_timelines:
            result["all_events"].append({
                "event_id": timeline.event_id,
                "sp_no": timeline.sp_no,
                "status": timeline.status,
                "status_text": {
                    1: "pending",
                    2: "approved", 
                    3: "rejected",
                    4: "cancelled"
                }.get(timeline.status, f"unknown({timeline.status})"),
                "created_at": timeline.created_at.isoformat()
            })
        
        # 错误记录
        for error in errors:
            result["errors"].append({
                "error_type": error.error_type,
                "error_message": error.error_message,
                "created_at": error.created_at.isoformat()
            })
        
        # 分析状态一致性
        if latest_timeline:
            expected_status = {
                1: "pending",
                2: "approved", 
                3: "rejected",
                4: "cancelled"
            }.get(latest_timeline.status)
            
            result["consistency_check"] = {
                "latest_event_status": expected_status,
                "quote_status": quote.status,
                "quote_approval_status": quote.approval_status,
                "status_matches": quote.status == expected_status,
                "approval_status_matches": quote.approval_status == expected_status
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调试查询失败: {str(e)}")


@router.get("/internal/debug/system")
async def debug_system_info(db: Session = Depends(get_db)):
    """
    系统信息调试
    """
    try:
        # 统计信息
        total_quotes = db.query(Quote).count()
        total_timelines = db.query(ApprovalTimeline).count()
        total_errors = db.query(ApprovalTimelineErrors).count()
        
        # 状态分布
        from sqlalchemy import func
        status_dist = db.query(Quote.status, func.count(Quote.id))\
            .group_by(Quote.status).all()
        
        # 最近的时间线事件
        recent_timelines = db.query(ApprovalTimeline)\
            .order_by(ApprovalTimeline.created_at.desc())\
            .limit(10).all()
        
        return {
            "system_info": {
                "db_path": os.path.abspath("app/test.db"),
                "process_id": os.getpid(),
                "instance_id": f"backend-{os.getpid()}",
                "working_directory": os.getcwd()
            },
            "statistics": {
                "total_quotes": total_quotes,
                "total_timelines": total_timelines,
                "total_errors": total_errors
            },
            "status_distribution": dict(status_dist),
            "recent_events": [
                {
                    "event_id": t.event_id,
                    "third_no": t.third_no,
                    "status": t.status,
                    "status_text": {
                        1: "pending",
                        2: "approved", 
                        3: "rejected",
                        4: "cancelled"
                    }.get(t.status, f"unknown({t.status})"),
                    "created_at": t.created_at.isoformat()
                } for t in recent_timelines
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统调试查询失败: {str(e)}")


@router.get("/internal/debug/signature-failures")
async def debug_signature_failures(db: Session = Depends(get_db)):
    """
    监控签名验证失败情况
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # 最近24小时的签名失败
        yesterday = datetime.now() - timedelta(hours=24)
        recent_failures = db.query(ApprovalTimelineErrors)\
            .filter(ApprovalTimelineErrors.error_type == "signature_verification_failed")\
            .filter(ApprovalTimelineErrors.created_at >= yesterday)\
            .order_by(ApprovalTimelineErrors.created_at.desc())\
            .all()
        
        # 最近7天按小时统计 (SQLite compatible)
        week_ago = datetime.now() - timedelta(days=7)
        hourly_stats = db.query(
            func.strftime('%Y-%m-%d %H:00:00', ApprovalTimelineErrors.created_at).label('hour'),
            func.count().label('count')
        ).filter(
            ApprovalTimelineErrors.error_type == "signature_verification_failed",
            ApprovalTimelineErrors.created_at >= week_ago
        ).group_by('hour').all()
        
        # 失败率计算（如果有成功记录的话）
        total_attempts_today = db.query(ApprovalTimeline)\
            .filter(ApprovalTimeline.created_at >= datetime.now().replace(hour=0, minute=0, second=0))\
            .count()
            
        failures_today = len([f for f in recent_failures 
                             if f.created_at >= datetime.now().replace(hour=0, minute=0, second=0)])
        
        failure_rate = (failures_today / (total_attempts_today + failures_today)) * 100 if (total_attempts_today + failures_today) > 0 else 0
        
        # 构建告警状态
        alert_status = "normal"
        alert_message = "签名验证正常"
        
        if failure_rate > 50:
            alert_status = "critical"
            alert_message = f"签名验证失败率过高: {failure_rate:.1f}%"
        elif failure_rate > 10:
            alert_status = "warning" 
            alert_message = f"签名验证失败率较高: {failure_rate:.1f}%"
        elif failures_today > 0:
            alert_status = "info"
            alert_message = f"今日有{failures_today}次签名验证失败"
        
        return {
            "monitoring_status": {
                "alert_level": alert_status,
                "message": alert_message,
                "failure_rate_24h": round(failure_rate, 2),
                "failures_today": failures_today,
                "successful_callbacks_today": total_attempts_today
            },
            "recent_failures": [
                {
                    "timestamp": f.created_at.isoformat(),
                    "error_message": f.error_message,
                    "request_data": f.request_data,
                    "error_type": f.error_type
                } for f in recent_failures[:20]  # 最近20个失败记录
            ],
            "hourly_statistics": [
                {
                    "hour": str(stat.hour),
                    "failure_count": stat.count
                } for stat in hourly_stats
            ],
            "recommendations": [
                "检查企业微信后台Token配置是否正确",
                "确认服务器时间与北京时间同步（NTP）",
                "验证AES Key长度为43位",
                "检查网络代理是否修改请求参数",
                "确认HTTPS证书有效性"
            ] if alert_status != "normal" else ["系统运行正常"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"签名失败监控查询失败: {str(e)}")