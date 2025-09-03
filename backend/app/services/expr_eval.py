from typing import Dict, Any

def safe_eval(expr: str, vars_dict: Dict[str, Any]) -> bool:
    """
    安全的表达式求值器 - 预定义模式
    
    Args:
        expr: 表达式字符串
        vars_dict: 变量字典
        
    Returns:
        表达式结果
    """
    amount = vars_dict.get("amount_total", 0) or 0
    
    # 预定义表达式映射 - 避免使用eval()
    expressions = {
        "amount_total >= 1000000": amount >= 1000000,
        "amount_total >= 500000": amount >= 500000,
        "amount_total >= 100000": amount >= 100000,
        "amount_total < 1000000": amount < 1000000,
        "amount_total < 500000": amount < 500000,
        "amount_total < 100000": amount < 100000,
    }
    
    return expressions.get(expr, False)

def validate_expression(expr: str) -> bool:
    """验证表达式是否被支持"""
    supported_expressions = [
        "amount_total >= 1000000",
        "amount_total >= 500000", 
        "amount_total >= 100000",
        "amount_total < 1000000",
        "amount_total < 500000",
        "amount_total < 100000"
    ]
    return expr in supported_expressions