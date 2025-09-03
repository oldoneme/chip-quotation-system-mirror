import yaml
import os
from typing import Dict, Any
from functools import lru_cache

class RulesLoader:
    """规则配置加载器"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "../config/approval_rules.yaml")
        self.config_path = config_path
        self._cache_timestamp = 0
        self._cached_rules = None
    
    @lru_cache(maxsize=1)
    def load_rules(self) -> Dict[str, Any]:
        """加载并缓存规则配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
            return rules
        except FileNotFoundError:
            # 返回默认配置
            return self._get_default_rules()
        except yaml.YAMLError as e:
            raise RuntimeError(f"YAML配置解析错误: {e}")
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """默认规则配置"""
        return {
            "templates": {
                "InquiryQuote": "TPL_inquiry",
                "ToolingQuote": "TPL_tooling",
                "EngineeringQuote": "TPL_engineering",
                "MassProductionQuote": "TPL_massprod",
                "ProcessQuote": "TPL_process",
                "ComprehensiveQuote": "TPL_comprehensive"
            },
            "routing": {
                "by_amount": [
                    {"when": "amount_total >= 500000", "approvers": ["finance_head", "ops_head"]},
                    {"when": "amount_total < 500000", "approvers": ["finance_mgr"]}
                ]
            },
            "fields": {"common": [], "extras": {}}
        }

# 全局实例
rules_loader = RulesLoader()

def get_rules() -> Dict[str, Any]:
    """获取规则配置的便捷函数"""
    return rules_loader.load_rules()