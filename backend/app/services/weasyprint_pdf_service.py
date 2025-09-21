"""
WeasyPrint PDF生成服务
专用于报价单PDF生成，支持6种报价类型的统一PDF输出:
1. 询价报价 (inquiry) - 简单表格显示
2. 工装夹具报价 (tooling) - 3类分组: 工装夹具清单、工程费用、量产准备费用
3. 工程机时报价 (engineering) - 2类分组: 机器设备、人员费用
4. 量产机时报价 (mass_production) - 2类分组: FT测试设备、其他设备
5. 量产工序报价 (process) - 2类分组: CP工序、FT工序
6. 综合报价 (comprehensive) - 通用表格显示
"""

from weasyprint import HTML, CSS
from decimal import Decimal
from typing import Dict, List, Optional
import os
from datetime import datetime


class WeasyPrintPDFService:
    """WeasyPrint PDF生成服务"""

    def __init__(self):
        """初始化PDF生成服务"""
        # 报价类型分类规则配置
        self.classification_rules = {
            '询价报价': {
                'method': 'default',
                'title': '📋 询价报价明细'
            },
            '工装夹具报价': {
                'method': 'category',
                'title': '📋 工装夹具报价明细',
                'categories': [
                    {
                        'name': '🔧 1. 工装夹具清单',
                        'filter': lambda item: (
                            item.get('unit') == '件' and
                            not any(keyword in (item.get('itemName', '') or '')
                                   for keyword in ['程序', '调试', '设计'])
                        ),
                        'columns': ['项目名称', '规格', '数量', '单位', '单价', '小计']
                    },
                    {
                        'name': '⚙️ 2. 工程费用',
                        'filter': lambda item: (
                            item.get('unit') == '项' and
                            any(keyword in (item.get('itemName', '') or '')
                               for keyword in ['测试程序', '程序开发', '夹具设计', '测试验证', '文档', '设计'])
                        ),
                        'columns': ['项目名称', '描述', '数量', '单位', '单价', '小计']
                    },
                    {
                        'name': '🏭 3. 量产准备费用',
                        'filter': lambda item: (
                            item.get('unit') == '项' and
                            any(keyword in (item.get('itemName', '') or '')
                               for keyword in ['调试', '校准', '检验', '设备调试', '调试费'])
                        ),
                        'columns': ['项目名称', '描述', '数量', '单位', '单价', '小计']
                    }
                ]
            },
            '工程机时报价': {
                'method': 'category',
                'title': '📋 工程机时报价明细',
                'categories': [
                    {
                        'name': '🔧 1. 机器设备',
                        'filter': lambda item: item.get('machineType') and item.get('machineType') != '人员',
                        'columns': ['设备类型', '设备型号', '描述', '数量', '单价', '小计']
                    },
                    {
                        'name': '👨‍💼 2. 人员费用',
                        'filter': lambda item: item.get('machineType') == '人员',
                        'columns': ['类型', '岗位/技能', '数量', '单价', '小计']
                    }
                ]
            },
            '量产机时报价': {
                'method': 'category',
                'title': '📋 量产机时报价明细',
                'categories': [
                    {
                        'name': '📱 FT测试设备',
                        'filter': lambda item: 'FT' in (item.get('itemDescription', '') or ''),
                        'columns': ['设备类型', '设备型号', '描述', '数量', '单价', '小计']
                    },
                    {
                        'name': '🔬 CP测试设备',
                        'filter': lambda item: 'CP' in (item.get('itemDescription', '') or ''),
                        'columns': ['设备类型', '设备型号', '描述', '数量', '单价', '小计']
                    },
                    {
                        'name': '🔧 辅助设备',
                        'filter': lambda item: (
                            item.get('machineType') == '辅助设备' or
                            (not ('FT' in (item.get('itemDescription', '') or '')) and
                             not ('CP' in (item.get('itemDescription', '') or '')) and
                             item.get('machineType') and
                             item.get('machineType') not in ['测试机', '分选机', '探针台'])
                        ),
                        'columns': ['设备类型', '设备型号', '描述', '数量', '单价', '小计']
                    }
                ]
            },
            '量产工序报价': {
                'method': 'category',
                'title': '📋 量产工序报价明细',
                'categories': [
                    {
                        'name': '🔍 1. CP工序',
                        'filter': lambda item: 'CP' in (item.get('itemDescription', '') or ''),
                        'columns': ['工序名称', '描述', '数量', '单价', '小计']
                    },
                    {
                        'name': '🔬 2. FT工序',
                        'filter': lambda item: 'FT' in (item.get('itemDescription', '') or '') and 'CP' not in (item.get('itemDescription', '') or ''),
                        'columns': ['工序名称', '描述', '数量', '单价', '小计']
                    }
                ]
            },
            '工序报价': {
                'method': 'category',
                'title': '📋 工序报价明细',
                'categories': [
                    {
                        'name': '🔍 1. CP工序',
                        'filter': lambda item: 'CP' in (item.get('itemDescription', '') or ''),
                        'columns': ['工序名称', '描述', '数量', '单价', '小计']
                    },
                    {
                        'name': '🔬 2. FT工序',
                        'filter': lambda item: 'FT' in (item.get('itemDescription', '') or '') and 'CP' not in (item.get('itemDescription', '') or ''),
                        'columns': ['工序名称', '描述', '数量', '单价', '小计']
                    }
                ]
            },
            '综合报价': {
                'method': 'default',
                'title': '📋 综合报价明细'
            }
        }

    def generate_quote_pdf(self, quote_data: Dict) -> bytes:
        """
        生成报价单PDF

        Args:
            quote_data: 报价单数据字典

        Returns:
            bytes: PDF文件二进制数据
        """
        try:
            # 生成HTML内容
            html_content = self._generate_html_content(quote_data)

            # 生成CSS样式
            css_content = self._generate_css_styles()

            # 使用WeasyPrint生成PDF，确保编码正确
            html_doc = HTML(string=html_content, encoding='utf-8')
            css_doc = CSS(string=css_content)

            pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc])

            return pdf_bytes

        except Exception as e:
            raise Exception(f"PDF生成失败: {str(e)}")

    def _generate_html_content(self, quote_data: Dict) -> str:
        """生成HTML内容 - 精确克隆前端Ant Design样式"""

        # 基本信息HTML
        basic_info_html = self._generate_basic_info_html(quote_data)

        # 报价明细HTML（根据类型）
        detail_html = self._generate_detail_html(quote_data)

        # 完整HTML结构
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>报价单 - {quote_data.get('quote_number', '')}</title>
    <style>
        {self._get_ant_design_css()}
    </style>
</head>
<body>
    <div class="quote-detail">
        <!-- 头部信息 -->
        <div class="ant-card detail-header">
            <div class="ant-card-body">
                <div class="header-left">
                    <h1>报价单详情</h1>
                    <div class="status-tags">
                        <span class="ant-tag">{self._get_status_display(quote_data)}</span>
                        <span class="ant-tag ant-tag-blue">{quote_data.get('type', '')}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 基本信息 -->
        {basic_info_html}

        <!-- 报价明细 -->
        {detail_html}

        <!-- 总计信息 -->
        <div class="total-section">
            <div class="total-amount">总计金额：¥{quote_data.get('total_amount', 0):.2f}</div>
        </div>
    </div>
</body>
</html>
        """

        return html_content

    def _generate_basic_info_html(self, quote_data: Dict) -> str:
        """生成基本信息HTML - 克隆Ant Design Descriptions组件"""

        return f"""
        <div class="ant-card info-section" style="margin-top: 16px;">
            <div class="ant-card-head">
                <div class="ant-card-head-wrapper">
                    <div class="ant-card-head-title">基本信息</div>
                </div>
            </div>
            <div class="ant-card-body">
                <div class="ant-descriptions ant-descriptions-bordered">
                    <div class="ant-descriptions-view">
                        <table class="ant-descriptions-table">
                            <tbody>
                                <tr class="ant-descriptions-row">
                                    <td class="ant-descriptions-item-label" colspan="1">报价单号</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('quote_number', '')}</td>
                                    <td class="ant-descriptions-item-label" colspan="1">客户</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('customer', '')}</td>
                                </tr>
                                <tr class="ant-descriptions-row">
                                    <td class="ant-descriptions-item-label" colspan="1">报价类型</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('type', '')}</td>
                                    <td class="ant-descriptions-item-label" colspan="1">币种</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('currency', 'RMB')}</td>
                                </tr>
                                <tr class="ant-descriptions-row">
                                    <td class="ant-descriptions-item-label" colspan="1">创建人</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('createdBy', '')}</td>
                                    <td class="ant-descriptions-item-label" colspan="1">创建时间</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('createdAt', '')}</td>
                                </tr>
                                <tr class="ant-descriptions-row">
                                    <td class="ant-descriptions-item-label" colspan="1">更新时间</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('updatedAt', '')}</td>
                                    <td class="ant-descriptions-item-label" colspan="1">有效期至</td>
                                    <td class="ant-descriptions-item-content" colspan="1">{quote_data.get('validUntil', '')}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                {self._generate_description_section(quote_data)}
            </div>
        </div>
        """

    def _generate_detail_html(self, quote_data: Dict) -> str:
        """根据报价类型生成明细HTML - 使用Ant Design卡片风格"""

        quote_type = quote_data.get('type', '')
        items = quote_data.get('items', [])

        # 开始报价明细卡片
        detail_html = f"""
        <div class="ant-card info-section">
            <div class="ant-card-head">
                <div class="ant-card-head-wrapper">
                    <div class="ant-card-head-title">报价明细</div>
                </div>
            </div>
            <div class="ant-card-body">
        """

        # 生成统一的明细内容
        detail_html += self._generate_items_table_html(items, quote_type)

        # 结束报价明细卡片
        detail_html += """
            </div>
        </div>
        """

        return detail_html

    def _generate_tooling_detail_html(self, items: List[Dict]) -> str:
        """生成工装夹具报价明细HTML"""

        # 筛选工装夹具项目
        tooling_items = [item for item in items
                        if item.get('unit') == '件' and
                        not any(keyword in (item.get('itemName', '') or '')
                               for keyword in ['程序', '调试', '设计'])]

        tooling_total = sum(item.get('totalPrice', 0) for item in tooling_items)

        tooling_rows = ""
        for item in tooling_items:
            tooling_rows += f"""
            <tr>
                <td>工装夹具</td>
                <td>{item.get('itemName', '')}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('totalPrice', 0):.2f}</td>
            </tr>
            """

        return f"""
        <div class="card detail-card">
            <div class="card-header">报价明细</div>
            <div class="card-body">
                <h4>🔧 工装夹具清单</h4>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>类别</th>
                            <th>项目名称</th>
                            <th>单价</th>
                            <th>数量</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tooling_rows}
                        <tr class="total-row">
                            <td colspan="4">工装夹具总价</td>
                            <td>¥{tooling_total:.2f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_engineering_detail_html(self, items: List[Dict]) -> str:
        """生成工程机时报价明细HTML"""

        # 筛选机器设备和人员
        machine_items = [item for item in items if item.get('machineType') and item.get('machineType') != '人员']
        personnel_items = [item for item in items if item.get('machineType') == '人员']

        machine_rows = ""
        for item in machine_items:
            machine_rows += f"""
            <tr>
                <td>{item.get('machineType', '')}</td>
                <td>{item.get('machineModel', '')}</td>
                <td>{item.get('itemDescription', '')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>¥{item.get('totalPrice', 0):.2f}</td>
            </tr>
            """

        personnel_rows = ""
        for item in personnel_items:
            personnel_rows += f"""
            <tr>
                <td>人员</td>
                <td>{item.get('itemDescription', '')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>¥{item.get('totalPrice', 0):.2f}</td>
            </tr>
            """

        return f"""
        <div class="card detail-card">
            <div class="card-header">报价明细</div>
            <div class="card-body">
                <h4>🔧 1. 机器设备</h4>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>设备类型</th>
                            <th>设备型号</th>
                            <th>描述</th>
                            <th>数量</th>
                            <th>单价</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {machine_rows}
                    </tbody>
                </table>

                <h4>👨‍💼 2. 人员费用</h4>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>类型</th>
                            <th>岗位/技能</th>
                            <th>数量</th>
                            <th>单价</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {personnel_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_mass_production_detail_html(self, items: List[Dict]) -> str:
        """生成量产机时报价明细HTML"""

        # 筛选FT和其他设备
        ft_items = [item for item in items if 'FT' in (item.get('itemDescription', '') or '')]
        other_items = [item for item in items if 'FT' not in (item.get('itemDescription', '') or '')]

        ft_rows = ""
        for item in ft_items:
            ft_rows += f"""
            <tr>
                <td>{item.get('machineType', '')}</td>
                <td>{item.get('machineModel', '')}</td>
                <td>{item.get('itemDescription', '')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>¥{item.get('totalPrice', 0):.2f}</td>
            </tr>
            """

        other_rows = ""
        for item in other_items:
            other_rows += f"""
            <tr>
                <td>{item.get('machineType', '')}</td>
                <td>{item.get('machineModel', '')}</td>
                <td>{item.get('itemDescription', '')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>¥{item.get('totalPrice', 0):.2f}</td>
            </tr>
            """

        return f"""
        <div class="card detail-card">
            <div class="card-header">报价明细</div>
            <div class="card-body">
                <h4>📱 FT测试设备</h4>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>设备类型</th>
                            <th>设备型号</th>
                            <th>描述</th>
                            <th>数量</th>
                            <th>单价</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ft_rows}
                    </tbody>
                </table>

                <h4>🔧 其他设备</h4>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>设备类型</th>
                            <th>设备型号</th>
                            <th>描述</th>
                            <th>数量</th>
                            <th>单价</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {other_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_process_detail_html(self, items: List[Dict]) -> str:
        """生成量产工序报价明细HTML"""

        # 分离CP和FT工序
        cp_items = [item for item in items if 'CP' in (item.get('itemDescription', '') or '')]
        ft_items = [item for item in items if 'FT' in (item.get('itemDescription', '') or '') and 'CP' not in (item.get('itemDescription', '') or '')]

        cp_rows = ""
        for item in cp_items:
            cp_rows += f"""
            <tr>
                <td>{item.get('itemDescription', '')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>¥{item.get('totalPrice', 0):.2f}</td>
            </tr>
            """

        ft_rows = ""
        for item in ft_items:
            ft_rows += f"""
            <tr>
                <td>{item.get('itemDescription', '')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>¥{item.get('totalPrice', 0):.2f}</td>
            </tr>
            """

        return f"""
        <div class="card detail-card">
            <div class="card-header">报价明细</div>
            <div class="card-body">
                <h4>🔬 CP工序</h4>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>工序描述</th>
                            <th>数量</th>
                            <th>单价</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cp_rows}
                    </tbody>
                </table>

                <h4>📱 FT工序</h4>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>工序描述</th>
                            <th>数量</th>
                            <th>单价</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ft_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_comprehensive_detail_html(self, items: List[Dict]) -> str:
        """生成综合报价明细HTML"""
        return self._generate_default_detail_html(items)

    def _generate_default_detail_html(self, items: List[Dict]) -> str:
        """生成默认表格明细HTML"""

        rows = ""
        total_amount = 0

        for item in items:
            total_price = item.get('totalPrice', 0)
            total_amount += total_price

            rows += f"""
            <tr>
                <td>{item.get('machineType', '')}</td>
                <td>{item.get('machineModel', '')}</td>
                <td>{item.get('itemDescription', '')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>¥{item.get('unitPrice', 0):.2f}</td>
                <td>¥{total_price:.2f}</td>
            </tr>
            """

        return f"""
        <div class="card detail-card">
            <div class="card-header">报价明细</div>
            <div class="card-body">
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>类别</th>
                            <th>型号</th>
                            <th>描述</th>
                            <th>数量</th>
                            <th>单价</th>
                            <th>小计</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                        <tr class="total-row">
                            <td colspan="5">总计</td>
                            <td>¥{total_amount:.2f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _generate_css_styles(self) -> str:
        """生成CSS样式"""

        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
                         'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #fff;
            color: #262626;
            line-height: 1.5;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        .card {
            background: #fff;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            margin-bottom: 16px;
            overflow: hidden;
            page-break-inside: avoid;
        }

        .card-header {
            background: #fafafa;
            border-bottom: 1px solid #d9d9d9;
            padding: 16px 24px;
            font-weight: 600;
            font-size: 16px;
            color: #262626;
        }

        .card-body {
            padding: 24px;
        }

        .descriptions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .descriptions-item {
            display: flex;
            margin-bottom: 12px;
        }

        .descriptions-label {
            font-weight: 500;
            color: #8c8c8c;
            width: 120px;
            flex-shrink: 0;
        }

        .descriptions-content {
            color: #262626;
            flex: 1;
        }

        .detail-card h4 {
            color: #1890ff;
            margin: 16px 0;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .detail-table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 14px;
        }

        .detail-table th,
        .detail-table td {
            border: 1px solid #f0f0f0;
            padding: 12px 8px;
            text-align: left;
        }

        .detail-table th {
            background: #fafafa;
            font-weight: 600;
            color: #262626;
        }

        .detail-table tbody tr:nth-child(even) {
            background: #fafafa;
        }

        .total-row {
            background: #f0f8ff !important;
            font-weight: bold;
            color: #1890ff;
        }

        .total-row td {
            border-top: 2px solid #1890ff;
        }

        /* 打印优化 */
        @media print {
            body {
                padding: 0;
            }

            .card {
                page-break-inside: avoid;
                margin-bottom: 20px;
            }

            .detail-table {
                page-break-inside: avoid;
            }

            .detail-table thead {
                display: table-header-group;
            }
        }
        """


    def _get_ant_design_css(self) -> str:
        """获取Ant Design风格的CSS样式"""
        return """
        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
                         'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
                         'Source Han Sans', 'SimSun', 'SimHei',
                         -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f0f2f5;
            color: #262626;
            line-height: 1.5;
            font-size: 14px;
        }

        .quote-detail {
            max-width: 800px;
            margin: 0 auto;
            background: #f0f2f5;
        }

        .ant-card {
            background: #fff;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            margin-bottom: 16px;
            overflow: hidden;
            page-break-inside: avoid;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
        }

        .ant-card-head {
            background: #fafafa;
            border-bottom: 1px solid #d9d9d9;
            padding: 16px 24px;
            margin: 0;
        }

        .ant-card-head-wrapper {
            display: flex;
            align-items: center;
        }

        .ant-card-head-title {
            font-weight: 600;
            font-size: 16px;
            color: #262626;
            margin: 0;
        }

        .ant-card-body {
            padding: 24px;
        }

        .detail-header {
            background: #fff;
            border: 1px solid #d9d9d9;
        }

        .header-left h1 {
            margin: 0 0 16px 0;
            font-size: 20px;
            font-weight: 600;
            color: #262626;
        }

        .status-tags {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .ant-tag {
            border-radius: 4px;
            padding: 4px 12px;
            font-size: 12px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            border: 1px solid #d9d9d9;
            background: #fafafa;
            color: #595959;
        }

        .ant-tag-blue {
            color: #1890ff;
            background: #f0f9ff;
            border-color: #91d5ff;
        }

        .ant-descriptions {
            width: 100%;
        }

        .ant-descriptions-bordered .ant-descriptions-view {
            border: 1px solid #f0f0f0;
            border-radius: 6px;
        }

        .ant-descriptions-table {
            width: 100%;
            border-collapse: collapse;
        }

        .ant-descriptions-row {
            border-bottom: 1px solid #f0f0f0;
        }

        .ant-descriptions-row:last-child {
            border-bottom: none;
        }

        .ant-descriptions-item-label {
            font-weight: 500;
            color: #8c8c8c;
            background: #fafafa;
            padding: 16px;
            border-right: 1px solid #f0f0f0;
            width: 25%;
            vertical-align: top;
        }

        .ant-descriptions-item-content {
            color: #262626;
            padding: 16px;
            border-right: 1px solid #f0f0f0;
            width: 25%;
            vertical-align: top;
            word-break: break-all;
        }

        .ant-descriptions-item-content:nth-child(4) {
            border-right: none;
        }

        .total-section {
            margin-top: 24px;
            text-align: right;
            padding: 16px 24px;
            background: #fff;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
        }

        .total-amount {
            font-size: 18px;
            font-weight: 600;
            color: #1890ff;
        }

        .detail-table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 14px;
        }

        .detail-table th,
        .detail-table td {
            border: 1px solid #f0f0f0;
            padding: 12px;
            text-align: left;
        }

        .detail-table th {
            background: #fafafa;
            font-weight: 600;
            color: #262626;
        }

        .detail-table tbody tr:hover {
            background: #f5f5f5;
        }

        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin: 24px 0 16px 0;
            color: #262626;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .item-card {
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            background: #fff;
            margin-bottom: 8px;
            padding: 12px;
        }

        .item-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .item-name {
            font-weight: 600;
            font-size: 13px;
            color: #262626;
        }

        .item-price {
            font-weight: 600;
            color: #1890ff;
            font-size: 14px;
        }

        .item-details {
            font-size: 12px;
            color: #666;
            line-height: 1.4;
        }

        .divider {
            border: none;
            border-top: 1px solid #f0f0f0;
            margin: 16px 0;
        }

        .description-section {
            margin-top: 16px;
        }

        .description-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #262626;
        }

        .description-content {
            color: #595959;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        /* 打印优化 */
        @media print {
            body {
                background: #fff;
                padding: 0;
            }

            .quote-detail {
                background: #fff;
            }

            .ant-card {
                box-shadow: none;
                page-break-inside: avoid;
            }

            .detail-table {
                page-break-inside: avoid;
            }

            .detail-table thead {
                display: table-header-group;
            }
        }
        """

    def _get_status_display(self, quote_data: Dict) -> str:
        """获取状态显示文本"""
        # 这里可以根据实际的状态来返回对应的显示文本
        return "草稿"  # 默认状态

    def _generate_description_section(self, quote_data: Dict) -> str:
        """生成描述部分HTML"""
        description = quote_data.get('description')
        if not description:
            return ""

        return f"""
        <div class="description-section">
            <hr class="divider">
            <div class="description-title">报价说明：</div>
            <div class="description-content">{description}</div>
        </div>
        """

    def _generate_items_table_html(self, items: List[Dict], quote_type: str) -> str:
        """生成报价明细表格HTML - 智能分类逻辑"""
        if not items:
            return """
            <div class="section-title">📋 报价明细</div>
            <div style="text-align: center; padding: 40px 20px; color: #999; font-size: 14px;">
                暂无报价明细
            </div>
            """

        # 获取分类规则
        rules = self.classification_rules.get(quote_type)
        if not rules:
            # 未知类型，使用默认显示
            return self._generate_smart_default_html(items, quote_type)

        # 根据分类方法生成HTML
        if rules['method'] == 'default':
            return self._generate_smart_default_html(items, quote_type, rules.get('title'))
        elif rules['method'] == 'category':
            return self._generate_smart_category_html(items, rules)
        else:
            return self._generate_smart_default_html(items, quote_type)


    def _generate_inquiry_quote_html(self, items: List[Dict]) -> str:
        """生成询价报价HTML - 使用默认单表格显示"""
        return self._generate_default_quote_html(items, '询价报价')

    def _generate_tooling_quote_html(self, items: List[Dict]) -> str:
        """生成工装夹具报价HTML - 分3类"""
        html = '<div class="section-title">📋 工装夹具报价明细</div>'

        # 1. 工装夹具清单
        tooling_items = [
            item for item in items
            if (item.get('unit') == '件' and
                not any(keyword in (item.get('itemName', '') or '')
                       for keyword in ['程序', '调试', '设计']))
        ]

        if tooling_items:
            html += self._generate_category_section('🔧 1. 工装夹具清单', tooling_items, ['项目名称', '规格', '数量', '单位', '单价', '小计'])

        # 2. 工程费用
        engineering_items = [
            item for item in items
            if (item.get('unit') == '项' and
                any(keyword in (item.get('itemName', '') or '')
                   for keyword in ['测试程序', '程序开发', '夹具设计', '测试验证', '文档', '设计']))
        ]

        if engineering_items:
            html += self._generate_category_section('⚙️ 2. 工程费用', engineering_items, ['项目名称', '描述', '数量', '单位', '单价', '小计'])

        # 3. 量产准备费用
        production_items = [
            item for item in items
            if (item.get('unit') == '项' and
                any(keyword in (item.get('itemName', '') or '')
                   for keyword in ['调试', '校准', '检验', '设备调试', '调试费']))
        ]

        if production_items:
            html += self._generate_category_section('🏭 3. 量产准备费用', production_items, ['项目名称', '描述', '数量', '单位', '单价', '小计'])

        return html

    def _generate_engineering_quote_html(self, items: List[Dict]) -> str:
        """生成工程机时报价HTML - 分机器设备类"""
        html = '<div class="section-title">📋 工程机时报价明细</div>'

        # 1. 机器设备
        machine_items = [
            item for item in items
            if item.get('machineType') and item.get('machineType') != '人员'
        ]

        if machine_items:
            html += self._generate_category_section('🔧 1. 机器设备', machine_items, ['设备型号', '设备类型', '单价(小时)', '描述'])

        return html

    def _generate_mass_production_quote_html(self, items: List[Dict]) -> str:
        """生成量产机时报价HTML - 分FT测试设备类"""
        html = '<div class="section-title">📋 量产机时报价明细</div>'

        # FT测试设备
        ft_items = [
            item for item in items
            if item.get('itemDescription') and 'FT' in item.get('itemDescription', '')
        ]

        if ft_items:
            html += self._generate_category_section('📱 FT测试设备', ft_items, ['设备名称', '设备类型', '单价(小时)', '描述'])

        return html

    def _generate_process_quote_html(self, items: List[Dict]) -> str:
        """生成量产工序报价HTML - 分CP工序和FT工序"""
        html = '<div class="section-title">📋 量产工序报价明细</div>'

        # CP工序
        cp_items = [
            item for item in items
            if any('CP' in (item.get(field, '') or '')
                  for field in ['itemName', 'itemDescription', 'machineType'])
        ]

        if cp_items:
            html += self._generate_category_section('🔬 CP工序', cp_items, ['工序名称', '设备类型', '数量', '单位', '单价', '小计'])

        # FT工序
        ft_items = [
            item for item in items
            if any('FT' in (item.get(field, '') or '')
                  for field in ['itemName', 'itemDescription', 'machineType'])
        ]

        if ft_items:
            html += self._generate_category_section('📱 FT工序', ft_items, ['工序名称', '设备类型', '数量', '单位', '单价', '小计'])

        return html

    def _generate_comprehensive_quote_html(self, items: List[Dict]) -> str:
        """生成综合报价HTML - 综合显示"""
        return self._generate_default_quote_html(items, '综合报价')

    def _generate_default_quote_html(self, items: List[Dict], quote_type: str) -> str:
        """生成默认报价HTML"""
        html = f'<div class="section-title">📋 {quote_type}明细</div>'
        html += self._generate_category_section('报价明细', items, ['项目名称', '设备型号', '描述', '数量', '单位', '单价', '小计'])
        return html

    def _generate_category_section(self, title: str, items: List[Dict], columns: List[str]) -> str:
        """生成分类段落HTML"""
        if not items:
            return ""

        html = f"""
        <div style="margin-bottom: 24px;">
            <h5 style="font-size: 14px; margin-bottom: 12px; color: #262626; font-weight: 600;">{title}</h5>
            <table class="detail-table">
                <thead>
                    <tr>
        """

        # 表头
        for column in columns:
            html += f'<th>{column}</th>'
        html += '</tr></thead><tbody>'

        # 表格内容
        for item in items:
            html += '<tr>'

            for column in columns:
                if column == '项目名称' or column == '工序名称':
                    value = item.get('itemName', item.get('itemDescription', '-'))
                elif column == '设备型号' or column == '设备名称':
                    value = item.get('machineModel', item.get('itemName', '-'))
                elif column == '设备类型':
                    value = item.get('machineType', '-')
                elif column == '规格' or column == '描述':
                    value = item.get('itemDescription', '-')
                elif column == '数量':
                    value = str(item.get('quantity', 0))
                elif column == '单位':
                    value = item.get('unit', '个')
                elif column == '单价' or column == '单价(小时)':
                    value = f"¥{item.get('unitPrice', 0):.2f}"
                elif column == '小计':
                    price = item.get('totalPrice', 0)
                    value = f"¥{price:.2f}"
                else:
                    value = '-'

                html += f'<td>{value}</td>'

            html += '</tr>'

        # 分类小计
        html += f"""
            </tbody>
        </table>
        <div style="text-align: right; margin-top: 8px; padding: 8px 12px; background: #f0f9ff; border-radius: 4px;">
            <span style="font-size: 14px; font-weight: 600; color: #1890ff;">
                {title}总价：¥{category_total:.2f}
            </span>
        </div>
        </div>
        """

        return html

    def _generate_smart_default_html(self, items: List[Dict], quote_type: str, title: str = None) -> str:
        """生成智能默认HTML - 单表格显示"""
        if not title:
            title = f'📋 {quote_type}明细'

        html = f'<div class="section-title">{title}</div>'

        # 生成统一表格
        html += '<div class="table-container">'
        html += '<table class="detail-table">'
        html += '<thead><tr>'
        html += '<th>项目名称</th>'
        html += '<th>描述</th>'
        html += '<th>数量</th>'
        html += '<th>单价</th>'
        html += '<th>小计</th>'
        html += '</tr></thead>'
        html += '<tbody>'

        total_amount = 0
        for item in items:
            item_name = item.get('itemName', '') or item.get('itemDescription', '')
            description = item.get('itemDescription', '') or item.get('machineModel', '')
            quantity = item.get('quantity', 0)
            unit_price = item.get('unitPrice', 0)
            total_price = item.get('totalPrice', 0)
            total_amount += total_price

            html += f'''
            <tr>
                <td>{item_name}</td>
                <td>{description}</td>
                <td>{quantity}</td>
                <td>¥{unit_price:.2f}</td>
                <td>¥{total_price:.2f}</td>
            </tr>
            '''

        # 总计行
        html += f'''
        <tr class="total-row">
            <td colspan="4">总计</td>
            <td>¥{total_amount:.2f}</td>
        </tr>
        '''
        html += '</tbody></table></div>'
        return html

    def _generate_smart_category_html(self, items: List[Dict], rules: Dict) -> str:
        """生成智能分类HTML - 多类别显示"""
        html = f'<div class="section-title">{rules["title"]}</div>'

        for category in rules['categories']:
            # 筛选该类别的项目
            category_items = [item for item in items if category['filter'](item)]

            if not category_items:
                continue

            # 生成类别标题和表格
            html += f'<div class="category-section">'
            html += f'<h4>{category["name"]}</h4>'
            html += '<table class="detail-table">'
            html += '<thead><tr>'

            # 动态生成表头
            for column in category['columns']:
                html += f'<th>{column}</th>'
            html += '</tr></thead>'
            html += '<tbody>'

            # 生成数据行
            for item in category_items:
                html += '<tr>'

                # 根据列名动态填充数据
                for column in category['columns']:
                    value = self._get_column_value(item, column)
                    html += f'<td>{value}</td>'

                html += '</tr>'

            html += '</tbody></table></div>'

        return html

    def _get_column_value(self, item: Dict, column: str) -> str:
        """根据列名获取对应的数据值"""
        column_mapping = {
            '项目名称': item.get('itemName', ''),
            '规格': item.get('machineModel', ''),
            '描述': item.get('itemDescription', ''),
            '设备类型': item.get('machineType', ''),
            '设备型号': item.get('machineModel', ''),
            '工序名称': item.get('itemName', '') or item.get('itemDescription', ''),
            '类型': '人员' if item.get('machineType') == '人员' else item.get('machineType', ''),
            '岗位/技能': item.get('itemDescription', ''),
            '数量': str(item.get('quantity', 0)),
            '单位': item.get('unit', ''),
            '单价': f"¥{item.get('unitPrice', 0):.2f}",
            '小计': f"¥{item.get('totalPrice', 0):.2f}"
        }

        return column_mapping.get(column, '')


# 创建服务实例
weasyprint_pdf_service = WeasyPrintPDFService()