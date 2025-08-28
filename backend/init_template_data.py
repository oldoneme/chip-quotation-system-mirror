#!/usr/bin/env python3
"""
初始化模板测试数据
"""

import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, QuoteTemplate, User

# 数据库连接
SQLALCHEMY_DATABASE_URL = "sqlite:///./app/test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_sample_templates():
    """创建示例模板"""
    db = SessionLocal()
    
    try:
        # 获取第一个用户作为创建者，如果没有就创建一个测试用户
        user = db.query(User).first()
        if not user:
            print("没有找到用户，创建测试用户...")
            user = User(
                userid="template_admin",
                name="模板管理员",
                email="admin@template.com",
                role="admin",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ 创建测试用户: {user.name}")
        
        # 询价报价模板
        inquiry_template_data = {
            "quote_type": "inquiry",
            "customer_info": {
                "customer_name": "[客户名称]",
                "customer_contact": "[联系人]",
                "customer_phone": "[联系电话]",
                "customer_email": "[邮箱地址]"
            },
            "pricing": {
                "currency": "CNY",
                "discount": 0,
                "tax_rate": 0.13,
                "payment_terms": "预付30%，验收后付清余款"
            },
            "items": [
                {
                    "item_name": "芯片功能测试",
                    "item_description": "全功能性能测试服务",
                    "machine_type": "测试机",
                    "supplier": "供应商A",
                    "machine_model": "Test-Model-01",
                    "unit": "小时",
                    "is_template_item": True
                },
                {
                    "item_name": "参数验证测试",
                    "item_description": "关键参数验证测试",
                    "machine_type": "测试机",
                    "supplier": "供应商B",
                    "machine_model": "Test-Model-02",
                    "unit": "小时",
                    "is_template_item": True
                }
            ],
            "settings": {
                "description_template": "本报价单用于芯片功能测试服务，包含完整的测试流程和质量保证。",
                "notes_template": "测试周期：根据具体项目确定\\n质量标准：符合行业标准\\n售后服务：提供3个月技术支持",
                "valid_days": 30
            }
        }
        
        inquiry_template = QuoteTemplate(
            name="标准询价报价模板",
            quote_type="inquiry",
            description="适用于一般询价项目的标准报价模板，包含基础测试项目和标准定价结构",
            template_data=json.dumps(inquiry_template_data, ensure_ascii=False),
            created_by=user.id
        )
        
        # 工程机时报价模板
        engineering_template_data = {
            "quote_type": "engineering",
            "customer_info": {
                "customer_name": "[客户名称]",
                "customer_contact": "[项目经理]",
                "customer_phone": "[联系电话]",
                "customer_email": "[项目邮箱]"
            },
            "pricing": {
                "currency": "CNY",
                "discount": 5,
                "tax_rate": 0.13,
                "payment_terms": "预付50%，阶段付款30%，验收后付清余款"
            },
            "items": [
                {
                    "item_name": "工程测试设备租用",
                    "item_description": "专业工程测试设备按小时计费",
                    "machine_type": "工程测试机",
                    "supplier": "工程设备供应商",
                    "machine_model": "Eng-Pro-500",
                    "unit": "小时",
                    "is_template_item": True
                },
                {
                    "item_name": "工程师技术服务",
                    "item_description": "高级工程师现场技术支持服务",
                    "machine_type": "人工服务",
                    "supplier": "技术团队",
                    "machine_model": "高级工程师",
                    "unit": "人天",
                    "is_template_item": True
                }
            ],
            "settings": {
                "description_template": "工程机时报价服务，提供专业的工程测试环境和技术支持，适用于复杂工程项目的测试需求。",
                "notes_template": "服务内容：\\n1. 专业设备提供\\n2. 技术人员支持\\n3. 测试报告编制\\n4. 问题诊断分析\\n\\n服务周期：根据项目规模确定\\n质量保证：符合工程标准",
                "valid_days": 45
            }
        }
        
        engineering_template = QuoteTemplate(
            name="工程机时标准模板",
            quote_type="engineering",
            description="适用于工程项目的机时报价模板，包含设备租用和工程师服务",
            template_data=json.dumps(engineering_template_data, ensure_ascii=False),
            created_by=user.id
        )
        
        # 量产机时报价模板
        mass_production_template_data = {
            "quote_type": "mass_production",
            "customer_info": {
                "customer_name": "[客户名称]",
                "customer_contact": "[生产经理]",
                "customer_phone": "[联系电话]",
                "customer_email": "[生产邮箱]"
            },
            "pricing": {
                "currency": "CNY",
                "discount": 10,
                "tax_rate": 0.13,
                "payment_terms": "月结30天"
            },
            "items": [
                {
                    "item_name": "量产测试线租用",
                    "item_description": "自动化量产测试设备线按小时计费",
                    "machine_type": "量产测试机",
                    "supplier": "自动化设备商",
                    "machine_model": "Auto-Test-Line-1000",
                    "unit": "小时",
                    "is_template_item": True
                },
                {
                    "item_name": "测试夹具使用",
                    "item_description": "专用测试夹具和工装设备使用费",
                    "machine_type": "测试夹具",
                    "supplier": "夹具供应商",
                    "machine_model": "Fixture-Pro-200",
                    "unit": "次",
                    "is_template_item": True
                }
            ],
            "settings": {
                "description_template": "量产机时报价服务，提供大批量生产测试环境，支持自动化测试流程，确保生产效率和质量。",
                "notes_template": "服务特点：\\n1. 自动化测试流程\\n2. 高效批量处理\\n3. 实时数据统计\\n4. 质量追溯系统\\n\\n生产能力：根据产品类型确定\\n质量标准：ISO质量体系",
                "valid_days": 60
            }
        }
        
        mass_production_template = QuoteTemplate(
            name="量产机时标准模板",
            quote_type="mass_production",
            description="适用于大批量生产的机时报价模板，支持自动化测试流程",
            template_data=json.dumps(mass_production_template_data, ensure_ascii=False),
            created_by=user.id
        )
        
        # 综合报价模板
        comprehensive_template_data = {
            "quote_type": "comprehensive",
            "customer_info": {
                "customer_name": "[客户名称]",
                "customer_contact": "[项目负责人]",
                "customer_phone": "[联系电话]",
                "customer_email": "[项目邮箱]"
            },
            "pricing": {
                "currency": "CNY",
                "discount": 8,
                "tax_rate": 0.13,
                "payment_terms": "分期付款，具体按合同约定"
            },
            "items": [
                {
                    "item_name": "项目咨询服务",
                    "item_description": "前期项目分析和技术咨询服务",
                    "machine_type": "咨询服务",
                    "supplier": "技术团队",
                    "machine_model": "专家咨询",
                    "unit": "人天",
                    "is_template_item": True
                },
                {
                    "item_name": "测试方案设计",
                    "item_description": "定制化测试方案设计和优化",
                    "machine_type": "技术服务",
                    "supplier": "设计团队",
                    "machine_model": "方案设计",
                    "unit": "项目",
                    "is_template_item": True
                },
                {
                    "item_name": "综合测试服务",
                    "item_description": "多种测试设备组合的综合服务",
                    "machine_type": "综合测试",
                    "supplier": "综合服务商",
                    "machine_model": "Multi-Test-Suite",
                    "unit": "小时",
                    "is_template_item": True
                }
            ],
            "settings": {
                "description_template": "综合报价服务，提供从项目咨询到测试执行的全流程服务，适用于复杂的综合性项目需求。",
                "notes_template": "服务范围：\\n1. 项目前期咨询\\n2. 测试方案设计\\n3. 设备资源配置\\n4. 测试执行管理\\n5. 报告编制交付\\n\\n项目周期：根据具体需求确定\\n服务保障：全程技术支持",
                "valid_days": 90
            }
        }
        
        comprehensive_template = QuoteTemplate(
            name="综合服务标准模板",
            quote_type="comprehensive",
            description="适用于综合性项目的全服务模板，包含咨询、设计、测试等全流程服务",
            template_data=json.dumps(comprehensive_template_data, ensure_ascii=False),
            created_by=user.id
        )
        
        # 添加所有模板到数据库
        templates = [
            inquiry_template,
            engineering_template,
            mass_production_template,
            comprehensive_template
        ]
        
        for template in templates:
            db.add(template)
        
        db.commit()
        
        print("✅ 成功创建示例模板:")
        for template in templates:
            print(f"  - {template.name} ({template.quote_type})")
        
    except Exception as e:
        print(f"❌ 创建模板失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    print("开始初始化模板数据...")
    create_sample_templates()
    print("模板数据初始化完成！")


if __name__ == "__main__":
    main()