#!/usr/bin/env python3
"""
企业微信回调处理端点 - 严格按照指令重写
按照安全模式处理：验签→AES解密→解析事件→幂等落库→写回状态→返回success
"""

from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
import json
from datetime import datetime

from ....database import get_db
from ....services.wecom_integration import WeComApprovalIntegration
from ....config import settings
from ....models import Quote, ApprovalTimeline
from ....utils.wecom_crypto import wecom_decrypt, wecom_signature
from ....utils.wecom_parser import parse_wecom_event
import os

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
    验证企业微信回调URL - GET验证
    严格按照企业微信规范：SHA1( sort(token, timestamp, nonce, echostr) ) → AES解密
    """
    print(f"🔍 GET验证回调 - 原始参数:")
    print(f"   msg_signature: {msg_signature}")
    print(f"   timestamp: {timestamp}")
    print(f"   nonce: {nonce}")
    print(f"   echostr(len): {len(echostr)}")
    
    try:
        # 验证签名 - GET模式使用echostr作为第四个参数
        calculated_signature = wecom_signature(
            settings.WECOM_CALLBACK_TOKEN, 
            timestamp, 
            nonce, 
            echostr
        )
        
        print(f"🔍 签名验证:")
        print(f"   calculated: {calculated_signature}")
        print(f"   received: {msg_signature}")
        
        if calculated_signature != msg_signature:
            # 详细记录签名验证失败信息
            failure_details = {
                "type": "GET_verification",
                "timestamp": timestamp,
                "nonce": nonce,
                "echostr_length": len(echostr),
                "received_signature": msg_signature,
                "calculated_signature": calculated_signature,
                "token_used": settings.WECOM_CALLBACK_TOKEN,
                "aes_key_length": len(settings.WECOM_ENCODING_AES_KEY),
                "corp_id": settings.WECOM_CORP_ID,
                "error_time": datetime.now().isoformat()
            }
            
            print(f"❌ GET验证 - 签名验证失败，详细信息:")
            print(json.dumps(failure_details, indent=2, ensure_ascii=False))
            
            # 记录到数据库（如果需要监控告警）
            try:
                from ....models import ApprovalTimelineErrors
                error_record = ApprovalTimelineErrors(
                    error_type="signature_verification_failed",
                    error_message=f"GET验证签名失败: {msg_signature} != {calculated_signature}",
                    request_data=json.dumps(failure_details),
                    created_at=datetime.now()
                )
                db.add(error_record)
                db.commit()
            except Exception as log_e:
                print(f"⚠️ 签名失败日志记录异常: {str(log_e)}")
                db.rollback()
            
            raise HTTPException(status_code=403, detail="签名验证失败")
        
        print(f"✅ GET验证 - 签名验证成功")
        
        # AES解密echostr
        decrypted = wecom_decrypt(
            settings.WECOM_ENCODING_AES_KEY, 
            echostr, 
            settings.WECOM_CORP_ID
        )
        
        result = decrypted.decode('utf-8')
        print(f"✅ GET验证 - AES解密成功: {result}")
        
        return PlainTextResponse(content=result)
        
    except HTTPException:
        raise  # 重新抛出HTTP异常（如签名验证失败）
    except Exception as e:
        # 记录详细的异常信息
        error_details = {
            "type": "GET_verification_exception",
            "timestamp": timestamp,
            "nonce": nonce,
            "error_message": str(e),
            "error_time": datetime.now().isoformat()
        }
        
        print(f"❌ GET验证 - 处理失败: {str(e)}")
        print(json.dumps(error_details, indent=2, ensure_ascii=False))
        
        # 记录到数据库
        try:
            from ....models import ApprovalTimelineErrors
            error_record = ApprovalTimelineErrors(
                error_type="get_verification_exception",
                error_message=str(e),
                request_data=json.dumps(error_details),
                created_at=datetime.now()
            )
            db.add(error_record)
            db.commit()
        except Exception as log_e:
            print(f"⚠️ 异常日志记录失败: {str(log_e)}")
            db.rollback()
        
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/approval")
async def handle_approval_callback(
    request: Request,
    msg_signature: str = Query(..., description="企业微信签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    db: Session = Depends(get_db)
):
    """
    处理企业微信审批回调 - POST事件
    严格按照安全模式：验签(含Encrypt)→AES解密→解析事件→幂等落库→写回状态→返回success
    """
    body = await request.body()
    
    print(f"🔍 POST事件回调 - 原始参数:")
    print(f"   msg_signature: {msg_signature}")
    print(f"   timestamp: {timestamp}")
    print(f"   nonce: {nonce}")
    print(f"   body(len): {len(body)}")
    
    try:
        # 分支兼容处理：查找Encrypt字段
        encrypted_msg = None
        plain_xml = None
        
        if body:
            # 尝试解析XML以查找Encrypt字段
            try:
                root = ET.fromstring(body)
                encrypt_elem = root.find("Encrypt")
                if encrypt_elem is not None and encrypt_elem.text:
                    encrypted_msg = encrypt_elem.text
                    print(f"🔍 发现加密消息 Encrypt字段，长度: {len(encrypted_msg)}")
                else:
                    plain_xml = body.decode('utf-8')
                    print(f"🔍 未发现Encrypt字段，尝试明文模式")
            except ET.ParseError:
                # 尝试JSON格式
                try:
                    data = json.loads(body)
                    encrypted_msg = data.get("Encrypt") or data.get("encrypt")
                    if encrypted_msg:
                        print(f"🔍 发现加密消息 JSON格式，长度: {len(encrypted_msg)}")
                except json.JSONDecodeError:
                    print(f"⚠️ 无法解析请求体格式")
                    return PlainTextResponse(content="failed")
        
        # 验证签名 - POST模式：含Encrypt或仅基础三参数
        if encrypted_msg:
            # 安全模式：使用Encrypt参与签名
            calculated_signature = wecom_signature(
                settings.WECOM_CALLBACK_TOKEN, 
                timestamp, 
                nonce, 
                encrypted_msg
            )
        else:
            # 极少数明文模式（容错）
            sign_str = "".join(sorted([settings.WECOM_CALLBACK_TOKEN, timestamp, nonce]))
            import hashlib
            calculated_signature = hashlib.sha1(sign_str.encode()).hexdigest()
        
        print(f"🔍 签名验证:")
        print(f"   calculated: {calculated_signature}")
        print(f"   received: {msg_signature}")
        
        if calculated_signature != msg_signature:
            # 详细记录签名验证失败信息
            failure_details = {
                "type": "POST_callback",
                "timestamp": timestamp,
                "nonce": nonce,
                "body_length": len(body),
                "has_encrypted_msg": encrypted_msg is not None,
                "encrypted_msg_length": len(encrypted_msg) if encrypted_msg else 0,
                "received_signature": msg_signature,
                "calculated_signature": calculated_signature,
                "token_used": settings.WECOM_CALLBACK_TOKEN,
                "aes_key_length": len(settings.WECOM_ENCODING_AES_KEY),
                "corp_id": settings.WECOM_CORP_ID,
                "error_time": datetime.now().isoformat(),
                "user_agent": request.headers.get("User-Agent", "Unknown"),
                "x_forwarded_for": request.headers.get("X-Forwarded-For", "None")
            }
            
            print(f"❌ POST事件 - 签名验证失败，详细信息:")
            print(json.dumps(failure_details, indent=2, ensure_ascii=False))
            
            # 记录到数据库（如果需要监控告警）
            try:
                from ....models import ApprovalTimelineErrors
                error_record = ApprovalTimelineErrors(
                    error_type="signature_verification_failed",
                    error_message=f"POST事件签名失败: {msg_signature} != {calculated_signature}",
                    request_data=json.dumps(failure_details),
                    created_at=datetime.now()
                )
                db.add(error_record)
                db.commit()
            except Exception as log_e:
                print(f"⚠️ 签名失败日志记录异常: {str(log_e)}")
                db.rollback()
            
            raise HTTPException(status_code=403, detail="签名验证失败")
        
        print(f"✅ POST事件 - 签名验证成功")
        
        # AES解密消息（如果是安全模式）
        if encrypted_msg:
            try:
                decrypted_bytes = wecom_decrypt(
                    settings.WECOM_ENCODING_AES_KEY,
                    encrypted_msg, 
                    settings.WECOM_CORP_ID
                )
                plain_content = decrypted_bytes.decode('utf-8')
                print(f"✅ POST事件 - AES解密成功")
            except Exception as decrypt_e:
                print(f"❌ POST事件 - AES解密失败: {str(decrypt_e)}")
                return PlainTextResponse(content="failed")
        else:
            plain_content = plain_xml
            print(f"✅ POST事件 - 使用明文内容")
        
        print(f"🔍 解密后内容预览: {plain_content[:200]}...")
        
        # 使用健壮解析器
        evt = parse_wecom_event(plain_content)
        
        # 提取关键信息
        msg_type = evt.get("msg_type")
        event = evt.get("event")
        event_id = evt.get("event_id")
        sp_no = evt.get("sp_no")
        third_no = evt.get("third_no")
        open_sp_status = evt.get("open_sp_status")
        parser_path = evt.get("parser_path", "")
        
        print(f"🔍 事件解析完成:")
        print(f"   MsgType: {msg_type}")
        print(f"   Event: {event}")
        print(f"   EventID: {event_id}")
        print(f"   SpNo: {sp_no}")
        print(f"   ThirdNo: {third_no}")
        print(f"   OpenSpStatus: {open_sp_status}")
        print(f"   ParserPath: {parser_path}")
        
        # 处理审批事件：sys_approval_change
        if (msg_type == "event" or event) and event == "sys_approval_change":
            # 幂等处理：先写入approval_timeline（EventID唯一约束）
            try:
                timeline = ApprovalTimeline(
                    event_id=event_id,
                    sp_no=sp_no,
                    third_no=third_no,
                    status=open_sp_status,
                    created_at=datetime.now()
                )
                db.add(timeline)
                db.commit()
                print(f"✅ 幂等写入 approval_timeline 成功")
                
            except Exception as timeline_e:
                # 可能是重复EventID，继续处理
                print(f"⚠️ approval_timeline 写入失败（可能重复）: {str(timeline_e)}")
                db.rollback()
            
            # 查找报价单
            quote = None
            if third_no:
                # 优先使用ThirdNo（报价单ID字符串）
                try:
                    quote_id = int(third_no)
                    quote = db.query(Quote).filter(Quote.id == quote_id).first()
                    print(f"✅ 通过ThirdNo找到报价单: {quote.quote_number if quote else 'None'}")
                except ValueError:
                    print(f"⚠️ ThirdNo不是有效的ID: {third_no}")
            
            if not quote and sp_no:
                # fallback使用SpNo
                quote = db.query(Quote).filter(Quote.wecom_approval_id == sp_no).first()
                print(f"✅ 通过SpNo找到报价单: {quote.quote_number if quote else 'None'}")
            
            if not quote:
                print(f"❌ 未找到对应的报价单")
                return PlainTextResponse(content="success")
            
            # 状态映射：1→Approving, 2→Approved, 3→Rejected, 4→Canceled
            status_mapping = {
                1: "pending",     # 审批中
                2: "approved",   # 已通过
                3: "rejected",   # 已拒绝  
                4: "cancelled"   # 已取消
            }
            
            new_status = status_mapping.get(open_sp_status)
            if not new_status:
                print(f"❌ 未知的审批状态: {open_sp_status}")
                
                # 尝试拉取详情兜底
                if sp_no:
                    print(f"🔄 尝试拉取审批详情兜底: SpNo={sp_no}")
                    try:
                        from ....services.wecom_integration import WeComApprovalIntegration
                        import asyncio
                        
                        async def fetch_detail():
                            wecom = WeComApprovalIntegration()
                            return await wecom.get_approval_detail(sp_no)
                        
                        # 调用获取审批详情API
                        detail = asyncio.run(fetch_detail())
                        
                        if detail and "info" in detail:
                            fallback_status = detail["info"].get("sp_status")
                            if fallback_status:
                                new_status = status_mapping.get(fallback_status)
                                if new_status:
                                    print(f"✅ 兜底成功，获取到状态: {fallback_status} -> {new_status}")
                                    open_sp_status = fallback_status
                                else:
                                    print(f"⚠️ 兜底状态仍然无法映射: {fallback_status}")
                            else:
                                print(f"⚠️ 详情中没有sp_status字段")
                        else:
                            print(f"⚠️ 获取详情失败或返回空")
                            
                    except Exception as e:
                        print(f"⚠️ 拉取详情失败: {str(e)}")
                
                # 如果仍然没有状态，返回success
                if not new_status:
                    # 记录解析失败到错误表
                    try:
                        from ....models import ApprovalTimelineErrors
                        error_record = ApprovalTimelineErrors(
                            error_type="parse_status_failed",
                            error_message=f"Unable to parse OpenSpStatus: {open_sp_status}, ParserPath: {parser_path}",
                            third_no=third_no,
                            sp_no=sp_no,
                            created_at=datetime.now()
                        )
                        db.add(error_record)
                        db.commit()
                    except Exception as log_e:
                        print(f"⚠️ 错误日志记录失败: {str(log_e)}")
                        db.rollback()
                    
                    return PlainTextResponse(content="success")
            
            # 更新报价单状态
            old_status = quote.status
            quote.status = new_status
            quote.approval_status = new_status
            quote.updated_at = datetime.now()
            
            try:
                db.commit()
                affected_rows = 1  # SQLAlchemy doesn't return affected rows easily
                print(f"✅ 更新报价单状态成功:")
                print(f"   报价单: {quote.quote_number}")
                print(f"   {old_status} → {new_status}")
                print(f"   受影响行数: {affected_rows}")
                
            except Exception as update_e:
                print(f"❌ 更新报价单状态失败: {str(update_e)}")
                db.rollback()
                return PlainTextResponse(content="failed")
            
            # 永远返回纯文本success，添加实例标识
            response = PlainTextResponse(content="success")
            response.headers["X-App-Instance"] = f"backend-{os.getpid()}"
            return response
        
        # 其他事件
        print(f"ℹ️ 其他事件类型，直接返回success")
        return PlainTextResponse(content="success")
        
    except HTTPException:
        raise  # 重新抛出HTTP异常（如签名验证失败）
    except Exception as e:
        # 记录详细的异常信息
        import traceback
        tb_str = traceback.format_exc()
        
        error_details = {
            "type": "POST_callback_exception",
            "timestamp": timestamp if 'timestamp' in locals() else "unknown",
            "nonce": nonce if 'nonce' in locals() else "unknown",
            "body_length": len(body) if 'body' in locals() else 0,
            "error_message": str(e),
            "traceback": tb_str,
            "error_time": datetime.now().isoformat()
        }
        
        print(f"❌ POST事件处理异常: {str(e)}")
        print(json.dumps(error_details, indent=2, ensure_ascii=False))
        print(tb_str)
        
        # 记录到数据库
        try:
            from ....models import ApprovalTimelineErrors
            error_record = ApprovalTimelineErrors(
                error_type="post_callback_exception",
                error_message=str(e),
                request_data=json.dumps(error_details),
                created_at=datetime.now()
            )
            db.add(error_record)
            db.commit()
        except Exception as log_e:
            print(f"⚠️ 异常日志记录失败: {str(log_e)}")
            db.rollback()
        
        return PlainTextResponse(content="failed")