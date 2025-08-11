"""
数据验证器模块
"""
from typing import Optional
from pydantic import validator
from app.core.config import settings


class MachineValidator:
    """机器数据验证器"""
    
    @staticmethod
    def validate_name(v: str) -> str:
        """验证机器名称"""
        if not v or len(v.strip()) < 2:
            raise ValueError('机器名称至少需要2个字符')
        if len(v.strip()) > 100:
            raise ValueError('机器名称不能超过100个字符')
        return v.strip()
    
    @staticmethod
    def validate_discount_rate(v: float) -> float:
        """验证折扣率"""
        if v is None:
            return 1.0
        if not settings.MIN_DISCOUNT_RATE <= v <= settings.MAX_DISCOUNT_RATE:
            raise ValueError(f'折扣率必须在{settings.MIN_DISCOUNT_RATE}到{settings.MAX_DISCOUNT_RATE}之间')
        return v
    
    @staticmethod
    def validate_exchange_rate(v: float, currency: str) -> float:
        """验证汇率"""
        if currency == 'RMB':
            return 1.0
        if currency == 'USD' and (v is None or v <= 0):
            return settings.DEFAULT_EXCHANGE_RATE_USD
        if v <= 0:
            raise ValueError('汇率必须大于0')
        return v
    
    @staticmethod
    def validate_currency(v: str) -> str:
        """验证货币类型"""
        valid_currencies = ['RMB', 'USD']
        if v not in valid_currencies:
            raise ValueError(f'货币类型必须是{valid_currencies}之一')
        return v


class CardConfigValidator:
    """板卡配置验证器"""
    
    @staticmethod
    def validate_part_number(v: Optional[str]) -> Optional[str]:
        """验证Part Number"""
        if v and len(v.strip()) > 50:
            raise ValueError('Part Number不能超过50个字符')
        return v.strip() if v else None
    
    @staticmethod
    def validate_board_name(v: Optional[str]) -> Optional[str]:
        """验证板卡名称"""
        if v and len(v.strip()) > 100:
            raise ValueError('板卡名称不能超过100个字符')
        return v.strip() if v else None
    
    @staticmethod
    def validate_unit_price(v: float) -> float:
        """验证单价"""
        if v < 0:
            raise ValueError('单价不能为负数')
        if v > 10000000:  # 1000万
            raise ValueError('单价超出合理范围')
        return v


class SupplierValidator:
    """供应商验证器"""
    
    @staticmethod
    def validate_name(v: str) -> str:
        """验证供应商名称"""
        if not v or len(v.strip()) < 2:
            raise ValueError('供应商名称至少需要2个字符')
        if len(v.strip()) > 100:
            raise ValueError('供应商名称不能超过100个字符')
        return v.strip()


class QuotationValidator:
    """报价验证器"""
    
    @staticmethod
    def validate_test_hours(v: float) -> float:
        """验证测试小时数"""
        if v <= 0:
            raise ValueError('测试小时数必须大于0')
        if v > 10000:  # 最多10000小时
            raise ValueError('测试小时数超出合理范围')
        return v
    
    @staticmethod
    def validate_quantity(v: int) -> int:
        """验证数量"""
        if v <= 0:
            raise ValueError('数量必须大于0')
        if v > 1000000:  # 最多100万
            raise ValueError('数量超出合理范围')
        return v
    
    @staticmethod
    def validate_engineering_rate(v: float) -> float:
        """验证工程系数"""
        if v <= 0:
            raise ValueError('工程系数必须大于0')
        if v > 10:
            raise ValueError('工程系数超出合理范围')
        return v