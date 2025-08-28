#!/usr/bin/env python3
"""
报价单导出服务
支持PDF和Excel格式导出
"""

import io
import os
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import pandas as pd
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from ..models import Quote
from ..schemas import Quote as QuoteSchema


class ExportService:
    """报价单导出服务"""

    def __init__(self, db: Session):
        self.db = db

    def export_quote_pdf(self, quote_id: int) -> StreamingResponse:
        """导出报价单为PDF格式"""
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="PDF导出功能不可用，请安装reportlab库: pip install reportlab"
            )

        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")

        # 创建PDF缓冲区
        buffer = io.BytesIO()
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # 构建PDF内容
        story = []
        styles = getSampleStyleSheet()
        
        # 标题
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # 居中对齐
            textColor=colors.darkblue
        )
        story.append(Paragraph("报价单", title_style))
        
        # 基本信息
        story.append(Spacer(1, 12))
        basic_info = [
            ['报价单号:', quote.quote_number],
            ['标题:', quote.title],
            ['客户名称:', quote.customer_name],
            ['报价类型:', self._get_quote_type_display(quote.quote_type)],
            ['创建时间:', quote.created_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['状态:', self._get_status_display(quote.status)]
        ]
        
        basic_table = Table(basic_info, colWidths=[2*inch, 4*inch])
        basic_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(basic_table)
        
        # 客户信息
        if quote.customer_contact or quote.customer_phone or quote.customer_email:
            story.append(Spacer(1, 20))
            story.append(Paragraph("客户信息", styles['Heading2']))
            
            customer_info = []
            if quote.customer_contact:
                customer_info.append(['联系人:', quote.customer_contact])
            if quote.customer_phone:
                customer_info.append(['联系电话:', quote.customer_phone])
            if quote.customer_email:
                customer_info.append(['邮箱:', quote.customer_email])
            if quote.customer_address:
                customer_info.append(['地址:', quote.customer_address])
            
            customer_table = Table(customer_info, colWidths=[2*inch, 4*inch])
            customer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(customer_table)
        
        # 报价明细
        if quote.items:
            story.append(Spacer(1, 20))
            story.append(Paragraph("报价明细", styles['Heading2']))
            
            # 明细表头
            items_data = [
                ['序号', '项目名称', '设备类型', '数量', '单位', '单价', '小计']
            ]
            
            # 明细数据
            for i, item in enumerate(quote.items, 1):
                items_data.append([
                    str(i),
                    item.item_name,
                    item.machine_type or '',
                    f'{item.quantity:.2f}',
                    item.unit,
                    f'¥{item.unit_price:.2f}',
                    f'¥{item.total_price:.2f}'
                ])
            
            items_table = Table(items_data, colWidths=[0.5*inch, 1.8*inch, 1.2*inch, 0.8*inch, 0.6*inch, 1*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(items_table)
        
        # 金额汇总
        story.append(Spacer(1, 20))
        story.append(Paragraph("金额汇总", styles['Heading2']))
        
        amount_info = [
            ['小计:', f'¥{quote.subtotal:.2f}'],
            ['折扣:', f'¥{quote.discount:.2f}'],
            ['税率:', f'{quote.tax_rate*100:.1f}%'],
            ['税额:', f'¥{quote.tax_amount:.2f}'],
            ['总金额:', f'¥{quote.total_amount:.2f}']
        ]
        
        amount_table = Table(amount_info, colWidths=[2*inch, 2*inch])
        amount_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
        ]))
        story.append(amount_table)
        
        # 备注信息
        if quote.description or quote.notes or quote.payment_terms:
            story.append(Spacer(1, 20))
            story.append(Paragraph("备注信息", styles['Heading2']))
            
            if quote.description:
                story.append(Paragraph(f"<b>报价说明:</b> {quote.description}", styles['Normal']))
                story.append(Spacer(1, 6))
            
            if quote.payment_terms:
                story.append(Paragraph(f"<b>付款条件:</b> {quote.payment_terms}", styles['Normal']))
                story.append(Spacer(1, 6))
            
            if quote.notes:
                story.append(Paragraph(f"<b>备注:</b> {quote.notes}", styles['Normal']))
        
        # 页脚
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            alignment=1,
            textColor=colors.grey
        )
        story.append(Paragraph(f"报价单生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
        
        # 构建PDF
        doc.build(story)
        buffer.seek(0)
        
        # 返回PDF响应
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=quote_{quote.quote_number}.pdf"}
        )

    def export_quote_excel(self, quote_id: int) -> StreamingResponse:
        """导出报价单为Excel格式"""
        if not PANDAS_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="Excel导出功能不可用，请安装pandas和openpyxl库: pip install pandas openpyxl"
            )

        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价单不存在")

        # 创建Excel缓冲区
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 基本信息工作表
            basic_data = {
                '项目': [
                    '报价单号', '标题', '客户名称', '报价类型', 
                    '联系人', '联系电话', '邮箱', '地址',
                    '创建时间', '状态', '币种'
                ],
                '内容': [
                    quote.quote_number,
                    quote.title,
                    quote.customer_name,
                    self._get_quote_type_display(quote.quote_type),
                    quote.customer_contact or '',
                    quote.customer_phone or '',
                    quote.customer_email or '',
                    quote.customer_address or '',
                    quote.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    self._get_status_display(quote.status),
                    quote.currency
                ]
            }
            
            basic_df = pd.DataFrame(basic_data)
            basic_df.to_excel(writer, sheet_name='基本信息', index=False)
            
            # 报价明细工作表
            if quote.items:
                items_data = []
                for i, item in enumerate(quote.items, 1):
                    items_data.append({
                        '序号': i,
                        '项目名称': item.item_name,
                        '项目描述': item.item_description or '',
                        '设备类型': item.machine_type or '',
                        '供应商': item.supplier or '',
                        '设备型号': item.machine_model or '',
                        '配置': item.configuration or '',
                        '数量': item.quantity,
                        '单位': item.unit,
                        '单价': item.unit_price,
                        '小计': item.total_price
                    })
                
                items_df = pd.DataFrame(items_data)
                items_df.to_excel(writer, sheet_name='报价明细', index=False)
            
            # 金额汇总工作表
            amount_data = {
                '项目': ['小计', '折扣', '税率(%)', '税额', '总金额'],
                '金额': [
                    quote.subtotal,
                    quote.discount,
                    quote.tax_rate * 100,
                    quote.tax_amount,
                    quote.total_amount
                ]
            }
            
            amount_df = pd.DataFrame(amount_data)
            amount_df.to_excel(writer, sheet_name='金额汇总', index=False)
            
            # 格式化工作表
            workbook = writer.book
            
            # 设置基本信息表格式
            basic_sheet = workbook['基本信息']
            basic_sheet.column_dimensions['A'].width = 15
            basic_sheet.column_dimensions['B'].width = 30
            
            # 设置明细表格式
            if quote.items:
                items_sheet = workbook['报价明细']
                for col in items_sheet.columns:
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 20)
                    items_sheet.column_dimensions[column].width = adjusted_width
            
            # 设置金额汇总表格式
            amount_sheet = workbook['金额汇总']
            amount_sheet.column_dimensions['A'].width = 15
            amount_sheet.column_dimensions['B'].width = 15

        buffer.seek(0)
        
        # 返回Excel响应
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=quote_{quote.quote_number}.xlsx"}
        )

    def export_quotes_summary_excel(self, quote_ids: list = None, status: str = None) -> StreamingResponse:
        """导出报价单汇总表"""
        if not PANDAS_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="Excel导出功能不可用，请安装pandas和openpyxl库"
            )

        # 构建查询条件
        query = self.db.query(Quote)
        
        if quote_ids:
            query = query.filter(Quote.id.in_(quote_ids))
        elif status:
            query = query.filter(Quote.status == status)
        
        quotes = query.order_by(Quote.created_at.desc()).all()
        
        if not quotes:
            raise HTTPException(status_code=404, detail="没有找到符合条件的报价单")

        # 准备数据
        summary_data = []
        for quote in quotes:
            summary_data.append({
                '报价单号': quote.quote_number,
                '标题': quote.title,
                '客户名称': quote.customer_name,
                '报价类型': self._get_quote_type_display(quote.quote_type),
                '状态': self._get_status_display(quote.status),
                '总金额': quote.total_amount,
                '币种': quote.currency,
                '创建时间': quote.created_at.strftime('%Y-%m-%d'),
                '提交时间': quote.submitted_at.strftime('%Y-%m-%d') if quote.submitted_at else '',
                '审批时间': quote.approved_at.strftime('%Y-%m-%d') if quote.approved_at else ''
            })

        # 创建Excel
        buffer = io.BytesIO()
        df = pd.DataFrame(summary_data)
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='报价单汇总', index=False)
            
            # 格式化
            workbook = writer.book
            sheet = workbook['报价单汇总']
            
            # 自动调整列宽
            for col in sheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 25)
                sheet.column_dimensions[column].width = adjusted_width

        buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=quotes_summary_{datetime.now().strftime('%Y%m%d')}.xlsx"}
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