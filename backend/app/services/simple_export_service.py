#!/usr/bin/env python3
"""
简化的报价单导出服务
不依赖第三方库，提供基本的导出功能
"""

import io
import json
import csv
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import StreamingResponse, Response

from ..models import Quote


class SimpleExportService:
    """简化的报价单导出服务"""

    def __init__(self, db: Session):
        self.db = db

    def export_quote_json(self, quote_id: int) -> Response:
        """导出报价单为JSON格式"""
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")

        # 构建导出数据
        export_data = {
            "basic_info": {
                "quote_number": quote.quote_number,
                "title": quote.title,
                "quote_type": self._get_quote_type_display(quote.quote_type),
                "customer_name": quote.customer_name,
                "customer_contact": quote.customer_contact,
                "customer_phone": quote.customer_phone,
                "customer_email": quote.customer_email,
                "customer_address": quote.customer_address,
                "currency": quote.currency,
                "status": self._get_status_display(quote.status),
                "version": quote.version,
                "created_at": quote.created_at.isoformat(),
                "updated_at": quote.updated_at.isoformat(),
            },
            "financial_info": {
                "subtotal": quote.subtotal,
                "discount": quote.discount,
                "tax_rate": quote.tax_rate,
                "tax_amount": quote.tax_amount,
                "total_amount": quote.total_amount,
                "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
                "payment_terms": quote.payment_terms
            },
            "items": [],
            "additional_info": {
                "description": quote.description,
                "notes": quote.notes,
                "submitted_at": quote.submitted_at.isoformat() if quote.submitted_at else None,
                "approved_at": quote.approved_at.isoformat() if quote.approved_at else None,
                "approved_by": quote.approved_by,
                "rejection_reason": quote.rejection_reason
            }
        }

        # 添加明细项目
        if quote.items:
            for item in quote.items:
                export_data["items"].append({
                    "item_name": item.item_name,
                    "item_description": item.item_description,
                    "machine_type": item.machine_type,
                    "supplier": item.supplier,
                    "machine_model": item.machine_model,
                    "configuration": item.configuration,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                })

        # 生成JSON
        json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=quote_{quote.quote_number}.json"}
        )

    def export_quote_csv(self, quote_id: int) -> StreamingResponse:
        """导出报价单为CSV格式"""
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")

        # 创建CSV缓冲区
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入基本信息
        writer.writerow(["基本信息"])
        writer.writerow(["报价单号", quote.quote_number])
        writer.writerow(["标题", quote.title])
        writer.writerow(["客户名称", quote.customer_name])
        writer.writerow(["报价类型", self._get_quote_type_display(quote.quote_type)])
        writer.writerow(["状态", self._get_status_display(quote.status)])
        writer.writerow(["币种", quote.currency])
        writer.writerow(["创建时间", quote.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])

        # 写入客户信息
        if quote.customer_contact or quote.customer_phone or quote.customer_email:
            writer.writerow(["客户信息"])
            if quote.customer_contact:
                writer.writerow(["联系人", quote.customer_contact])
            if quote.customer_phone:
                writer.writerow(["联系电话", quote.customer_phone])
            if quote.customer_email:
                writer.writerow(["邮箱", quote.customer_email])
            if quote.customer_address:
                writer.writerow(["地址", quote.customer_address])
            writer.writerow([])

        # 写入报价明细
        if quote.items:
            writer.writerow(["报价明细"])
            writer.writerow(["序号", "项目名称", "设备类型", "供应商", "设备型号", "数量", "单位", "单价", "小计"])
            
            for i, item in enumerate(quote.items, 1):
                writer.writerow([
                    i,
                    item.item_name,
                    item.machine_type or '',
                    item.supplier or '',
                    item.machine_model or '',
                    item.quantity,
                    item.unit,
                    item.unit_price,
                    item.total_price
                ])
            writer.writerow([])

        # 写入金额汇总
        writer.writerow(["金额汇总"])
        writer.writerow(["小计", quote.subtotal])
        writer.writerow(["折扣", quote.discount])
        writer.writerow(["税率(%)", quote.tax_rate * 100])
        writer.writerow(["税额", quote.tax_amount])
        writer.writerow(["总金额", quote.total_amount])
        writer.writerow([])

        # 写入备注信息
        if quote.description or quote.notes or quote.payment_terms:
            writer.writerow(["备注信息"])
            if quote.description:
                writer.writerow(["报价说明", quote.description])
            if quote.payment_terms:
                writer.writerow(["付款条件", quote.payment_terms])
            if quote.notes:
                writer.writerow(["备注", quote.notes])

        # 准备下载
        output.seek(0)
        csv_content = output.getvalue()
        output.close()

        # 返回CSV响应
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=quote_{quote.quote_number}.csv"}
        )

    def export_quote_html(self, quote_id: int) -> Response:
        """导出报价单为HTML格式"""
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")

        # 构建HTML内容
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>报价单 - {quote.quote_number}</title>
    <style>
        body {{ font-family: Arial, 'SimSun', sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .section {{ margin-bottom: 25px; }}
        .section h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
        .info-table td {{ padding: 8px 12px; border: 1px solid #ddd; }}
        .info-table td:first-child {{ font-weight: bold; background-color: #f8f9fa; width: 150px; }}
        .items-table {{ width: 100%; border-collapse: collapse; }}
        .items-table th, .items-table td {{ padding: 10px; border: 1px solid #ddd; text-align: center; }}
        .items-table th {{ background-color: #3498db; color: white; }}
        .amount-table {{ width: 400px; margin-left: auto; }}
        .total-row {{ font-weight: bold; background-color: #f8f9fa; }}
        .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #7f8c8d; }}
        @media print {{
            body {{ margin: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>报价单</h1>
        <p style="font-size: 18px; color: #7f8c8d;">Quote Number: {quote.quote_number}</p>
    </div>

    <div class="section">
        <h2>基本信息</h2>
        <table class="info-table">
            <tr><td>报价单号</td><td>{quote.quote_number}</td></tr>
            <tr><td>标题</td><td>{quote.title}</td></tr>
            <tr><td>客户名称</td><td>{quote.customer_name}</td></tr>
            <tr><td>报价类型</td><td>{self._get_quote_type_display(quote.quote_type)}</td></tr>
            <tr><td>状态</td><td>{self._get_status_display(quote.status)}</td></tr>
            <tr><td>币种</td><td>{quote.currency}</td></tr>
            <tr><td>创建时间</td><td>{quote.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>
    </div>
"""

        # 客户信息
        if quote.customer_contact or quote.customer_phone or quote.customer_email:
            html_content += """
    <div class="section">
        <h2>客户信息</h2>
        <table class="info-table">
"""
            if quote.customer_contact:
                html_content += f"            <tr><td>联系人</td><td>{quote.customer_contact}</td></tr>\n"
            if quote.customer_phone:
                html_content += f"            <tr><td>联系电话</td><td>{quote.customer_phone}</td></tr>\n"
            if quote.customer_email:
                html_content += f"            <tr><td>邮箱</td><td>{quote.customer_email}</td></tr>\n"
            if quote.customer_address:
                html_content += f"            <tr><td>地址</td><td>{quote.customer_address}</td></tr>\n"
            
            html_content += """        </table>
    </div>
"""

        # 报价明细
        if quote.items:
            html_content += """
    <div class="section">
        <h2>报价明细</h2>
        <table class="items-table">
            <thead>
                <tr>
                    <th>序号</th>
                    <th>项目名称</th>
                    <th>设备类型</th>
                    <th>供应商</th>
                    <th>设备型号</th>
                    <th>数量</th>
                    <th>单位</th>
                    <th>单价</th>
                    <th>小计</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for i, item in enumerate(quote.items, 1):
                html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{item.item_name}</td>
                    <td>{item.machine_type or ''}</td>
                    <td>{item.supplier or ''}</td>
                    <td>{item.machine_model or ''}</td>
                    <td>{item.quantity:.2f}</td>
                    <td>{item.unit}</td>
                    <td>¥{item.unit_price:.2f}</td>
                    <td>¥{item.total_price:.2f}</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
    </div>
"""

        # 金额汇总
        html_content += f"""
    <div class="section">
        <h2>金额汇总</h2>
        <table class="info-table amount-table">
            <tr><td>小计</td><td>¥{quote.subtotal:.2f}</td></tr>
            <tr><td>折扣</td><td>¥{quote.discount:.2f}</td></tr>
            <tr><td>税率</td><td>{quote.tax_rate*100:.1f}%</td></tr>
            <tr><td>税额</td><td>¥{quote.tax_amount:.2f}</td></tr>
            <tr class="total-row"><td>总金额</td><td>¥{quote.total_amount:.2f}</td></tr>
        </table>
    </div>
"""

        # 备注信息
        if quote.description or quote.notes or quote.payment_terms:
            html_content += """
    <div class="section">
        <h2>备注信息</h2>
        <table class="info-table">
"""
            if quote.description:
                html_content += f"            <tr><td>报价说明</td><td>{quote.description}</td></tr>\n"
            if quote.payment_terms:
                html_content += f"            <tr><td>付款条件</td><td>{quote.payment_terms}</td></tr>\n"
            if quote.notes:
                html_content += f"            <tr><td>备注</td><td>{quote.notes}</td></tr>\n"
            
            html_content += """        </table>
    </div>
"""

        # 页脚
        html_content += f"""
    <div class="footer">
        <p>报价单生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>此报价单由芯片测试报价系统自动生成</p>
    </div>
</body>
</html>
"""

        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=quote_{quote.quote_number}.html"}
        )

    def export_quotes_summary_csv(self, quote_ids: list = None, status: str = None) -> StreamingResponse:
        """导出报价单汇总为CSV格式"""
        # 构建查询条件
        query = self.db.query(Quote)
        
        if quote_ids:
            query = query.filter(Quote.id.in_(quote_ids))
        elif status:
            query = query.filter(Quote.status == status)
        
        quotes = query.order_by(Quote.created_at.desc()).all()
        
        if not quotes:
            raise HTTPException(status_code=404, detail="没有找到符合条件的报价单")

        # 创建CSV缓冲区
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入标题行
        writer.writerow([
            "报价单号", "标题", "客户名称", "报价类型", "状态", "总金额", "币种",
            "创建时间", "提交时间", "审批时间", "创建人"
        ])

        # 写入数据行
        for quote in quotes:
            writer.writerow([
                quote.quote_number,
                quote.title,
                quote.customer_name,
                self._get_quote_type_display(quote.quote_type),
                self._get_status_display(quote.status),
                quote.total_amount,
                quote.currency,
                quote.created_at.strftime('%Y-%m-%d'),
                quote.submitted_at.strftime('%Y-%m-%d') if quote.submitted_at else '',
                quote.approved_at.strftime('%Y-%m-%d') if quote.approved_at else '',
                f"用户{quote.created_by}"
            ])

        # 准备下载
        output.seek(0)
        csv_content = output.getvalue()
        output.close()

        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=quotes_summary_{datetime.now().strftime('%Y%m%d')}.csv"}
        )

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

    def _get_status_display(self, status: str) -> str:
        """获取状态显示名称"""
        status_map = {
            'draft': '草稿',
            'pending': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝'
        }
        return status_map.get(status, status)