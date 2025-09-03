"""
企业微信审批配置模块
定义审批模板映射、规则和消息格式
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# 报价类型到审批模板ID的映射
APPROVAL_TEMPLATES = {
    "InquiryQuote": "inquiry_template",           # 询价报价模板
    "ToolingQuote": "tooling_template",           # 工装夹具报价模板  
    "EngineeringQuote": "engineering_template",    # 工程机时报价模板
    "MassProductionQuote": "production_template",  # 量产机时报价模板
    "ProcessQuote": "process_template",           # 量产工序报价模板
    "ComprehensiveQuote": "comprehensive_template" # 综合报价模板
}

# 报价类型显示名称映射
QUOTE_TYPE_NAMES = {
    "InquiryQuote": "询价报价",
    "ToolingQuote": "工装夹具报价", 
    "EngineeringQuote": "工程机时报价",
    "MassProductionQuote": "量产机时报价",
    "ProcessQuote": "量产工序报价",
    "ComprehensiveQuote": "综合报价"
}

@dataclass
class ApprovalRule:
    """审批规则数据类"""
    min_amount: float = 0.0
    max_amount: float = float('inf')
    approvers: List[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.approvers is None:
            self.approvers = []


# 基于金额的审批规则 (按优先级排序)
AMOUNT_RULES = [
    ApprovalRule(
        min_amount=1000000,  # 100万以上
        approvers=["finance_head", "ops_head", "ceo"],
        description="超大额报价，需要财务总监+运营总监+CEO审批"
    ),
    ApprovalRule(
        min_amount=500000,   # 50万-100万
        max_amount=1000000,
        approvers=["finance_mgr", "ops_mgr", "finance_head"],
        description="大额报价，需要财务经理+运营经理+财务总监审批"
    ),
    ApprovalRule(
        min_amount=100000,   # 10万-50万
        max_amount=500000,
        approvers=["finance_mgr", "ops_mgr"],
        description="中等金额报价，需要财务经理+运营经理审批"
    ),
    ApprovalRule(
        min_amount=0,        # 10万以下
        max_amount=100000,
        approvers=["finance_mgr"],
        description="小额报价，需要财务经理审批"
    )
]

# 特殊类型的审批规则覆盖
SPECIAL_TYPE_RULES = {
    "ComprehensiveQuote": {
        "min_approvers": ["finance_mgr", "ops_mgr"],  # 综合报价最少需要两人审批
        "description": "综合报价需要特殊审批流程"
    },
    "ProcessQuote": {
        "additional_approvers": ["tech_lead"],        # 工序报价需要技术负责人参与
        "description": "工序报价需要技术负责人参与审批"
    }
}

# 审批消息模板
APPROVAL_MESSAGE_TEMPLATES = {
    "title": "【报价审批】{quote_type} / {quote_number}",
    "content": """
报价类型：{quote_type}
报价单号：{quote_number}
客户名称：{customer_name}
报价金额：{currency} {total_amount:,.2f}
创建人员：{creator_name}
提交时间：{submit_time}

点击查看详情：{detail_link}
""",
    "simple_content": "客户：{customer_name} | 金额：{currency} {total_amount:,.2f} | 创建人：{creator_name}"
}

# 审批表单字段映射 (企业微信审批模板字段)
APPROVAL_FORM_FIELDS = {
    "common": [
        {"key": "quote_type", "label": "报价类型", "control": "Text", "id": "Text-1"},
        {"key": "quote_number", "label": "报价单号", "control": "Text", "id": "Text-2"}, 
        {"key": "customer_name", "label": "客户名称", "control": "Text", "id": "Text-3"},
        {"key": "description", "label": "报价说明", "control": "Textarea", "id": "Text-4"},
        {"key": "total_amount", "label": "报价金额", "control": "Money", "id": "Money-1"},
        {"key": "detail_link", "label": "详情链接", "control": "Text", "id": "Text-5"}
    ],
    "extras": {
        "ProcessQuote": [
            {"key": "process_count", "label": "工序数量", "control": "Number", "id": "Number-1"},
            {"key": "estimated_hours", "label": "预计工时", "control": "Number", "id": "Number-2"}
        ],
        "EngineeringQuote": [
            {"key": "hourly_rate", "label": "小时费率", "control": "Money", "id": "Money-2"},
            {"key": "estimated_hours", "label": "预计工时", "control": "Number", "id": "Number-1"}
        ]
    }
}

# 审批状态映射
APPROVAL_STATUS_MAPPING = {
    # 企业微信状态 -> 系统状态
    "1": "pending",        # 审批中
    "2": "approved",       # 已通过  
    "3": "rejected",       # 已驳回
    "4": "cancelled",      # 已撤销
    "6": "pending",        # 通过后撤销(重新审批)
    "7": "expired",        # 已过期
    "10": "pending"        # 审批中(有人已审)
}

# 系统状态显示名称
STATUS_DISPLAY_NAMES = {
    "draft": "草稿",
    "pending": "审批中", 
    "approved": "已通过",
    "rejected": "已驳回",
    "cancelled": "已撤销",
    "expired": "已过期",
    "completed": "已完成"
}


def get_template_by_quote_type(quote_type: str) -> str:
    """根据报价类型获取审批模板ID"""
    return APPROVAL_TEMPLATES.get(quote_type, "default_template")


def get_quote_type_display_name(quote_type: str) -> str:
    """获取报价类型显示名称"""
    return QUOTE_TYPE_NAMES.get(quote_type, quote_type)


def get_approvers_by_amount(amount: float, quote_type: str = None) -> List[str]:
    """根据金额和报价类型获取审批人列表"""
    # 首先按金额规则选择审批人
    base_approvers = []
    for rule in AMOUNT_RULES:
        if rule.min_amount <= amount < rule.max_amount:
            base_approvers = rule.approvers.copy()
            break
    
    # 如果没有找到匹配规则，使用默认
    if not base_approvers:
        base_approvers = ["finance_mgr"]
    
    # 应用特殊类型规则
    if quote_type and quote_type in SPECIAL_TYPE_RULES:
        special_rule = SPECIAL_TYPE_RULES[quote_type]
        
        # 添加额外审批人
        if "additional_approvers" in special_rule:
            base_approvers.extend(special_rule["additional_approvers"])
        
        # 确保最少审批人
        if "min_approvers" in special_rule:
            for approver in special_rule["min_approvers"]:
                if approver not in base_approvers:
                    base_approvers.append(approver)
    
    # 去重并保持顺序
    unique_approvers = []
    for approver in base_approvers:
        if approver not in unique_approvers:
            unique_approvers.append(approver)
    
    return unique_approvers


def get_approval_message_data(quote: Any, detail_link: str) -> Dict[str, Any]:
    """构建审批消息数据"""
    from datetime import datetime
    
    return {
        "quote_type": get_quote_type_display_name(getattr(quote, 'quote_type', '')),
        "quote_number": getattr(quote, 'quote_number', ''),
        "customer_name": getattr(quote, 'customer_name', ''),
        "currency": "¥" if getattr(quote, 'currency', 'CNY') == 'CNY' else "$",
        "total_amount": getattr(quote, 'total_amount', 0) or 0,
        "creator_name": getattr(quote.creator, 'name', '') if hasattr(quote, 'creator') and quote.creator else '系统用户',
        "submit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "detail_link": detail_link
    }


def get_approval_form_data(quote: Any, detail_link: str) -> List[Dict[str, Any]]:
    """构建企业微信审批表单数据"""
    message_data = get_approval_message_data(quote, detail_link)
    
    # 基础表单字段
    form_contents = []
    for field in APPROVAL_FORM_FIELDS["common"]:
        value = ""
        if field["key"] in message_data:
            if field["control"] == "Money":
                value = {"new_money": str(int(message_data[field["key"]] * 100))}  # 企业微信金额单位是分
            else:
                value = {"text": str(message_data[field["key"]])}
        
        form_contents.append({
            "control": field["control"],
            "id": field["id"],
            "value": value
        })
    
    # 添加特殊类型的额外字段
    quote_type = getattr(quote, 'quote_type', '')
    if quote_type in APPROVAL_FORM_FIELDS["extras"]:
        for field in APPROVAL_FORM_FIELDS["extras"][quote_type]:
            value = {"text": ""}  # 默认空值，后续可以扩展
            form_contents.append({
                "control": field["control"], 
                "id": field["id"],
                "value": value
            })
    
    return form_contents


def map_wecom_status_to_system(wecom_status: str) -> str:
    """将企业微信状态映射为系统状态"""
    return APPROVAL_STATUS_MAPPING.get(str(wecom_status), "pending")


def get_status_display_name(status: str) -> str:
    """获取状态显示名称"""
    return STATUS_DISPLAY_NAMES.get(status, status)