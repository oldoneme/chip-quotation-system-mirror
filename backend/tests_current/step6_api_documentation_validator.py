#!/usr/bin/env python3
"""
Step 6.3: API文档验证器
验证统一审批系统的API文档完整性和准确性
"""

import os
import sys
import json
import inspect
from datetime import datetime
from typing import Dict, List, Any

def validate_api_documentation():
    """验证API文档"""
    print("📚 Step 6.3: 验证API文档")
    print("="*60)

    results = {
        "endpoint_documentation": {},
        "model_documentation": {},
        "service_documentation": {},
        "openapi_schema": {}
    }

    # 1. 验证端点文档
    print("\n🔍 1. 验证API端点文档...")
    results["endpoint_documentation"] = validate_endpoint_docs()

    # 2. 验证数据模型文档
    print("\n🔍 2. 验证数据模型文档...")
    results["model_documentation"] = validate_model_docs()

    # 3. 验证服务文档
    print("\n🔍 3. 验证服务文档...")
    results["service_documentation"] = validate_service_docs()

    # 4. 生成OpenAPI架构验证
    print("\n🔍 4. 验证OpenAPI架构...")
    results["openapi_schema"] = validate_openapi_schema()

    return results

def validate_endpoint_docs():
    """验证端点文档"""
    try:
        from app.api.v1.endpoints.approval import router

        endpoint_docs = {}

        # 检查路由器中的端点
        routes = router.routes
        print(f"   📊 发现 {len(routes)} 个端点")

        for route in routes:
            if hasattr(route, 'endpoint'):
                endpoint_name = route.endpoint.__name__
                docstring = route.endpoint.__doc__

                endpoint_docs[endpoint_name] = {
                    "has_docstring": bool(docstring and docstring.strip()),
                    "docstring_length": len(docstring.strip()) if docstring else 0,
                    "path": getattr(route, 'path', 'unknown'),
                    "methods": getattr(route, 'methods', [])
                }

                if docstring and docstring.strip():
                    print(f"      ✅ {endpoint_name}: 有文档 ({len(docstring.strip())} 字符)")
                else:
                    print(f"      ❌ {endpoint_name}: 缺少文档")

        return endpoint_docs

    except Exception as e:
        print(f"   ❌ 端点文档验证失败: {e}")
        return {"error": str(e)}

def validate_model_docs():
    """验证数据模型文档"""
    try:
        from app.api.v1.endpoints.approval import ApprovalRequest, RejectRequest

        model_docs = {}
        models = [ApprovalRequest, RejectRequest]

        print(f"   📊 检查 {len(models)} 个数据模型")

        for model in models:
            model_name = model.__name__
            docstring = model.__doc__

            # 获取字段信息
            fields = {}
            if hasattr(model, '__fields__'):
                for field_name, field_info in model.__fields__.items():
                    fields[field_name] = {
                        "type": str(field_info.type_),
                        "required": field_info.required,
                        "default": str(field_info.default) if hasattr(field_info, 'default') else None
                    }

            model_docs[model_name] = {
                "has_docstring": bool(docstring and docstring.strip()),
                "docstring_length": len(docstring.strip()) if docstring else 0,
                "fields": fields,
                "field_count": len(fields)
            }

            if docstring and docstring.strip():
                print(f"      ✅ {model_name}: 有文档，{len(fields)} 个字段")
            else:
                print(f"      ⚠️ {model_name}: 缺少类文档，{len(fields)} 个字段")

        return model_docs

    except Exception as e:
        print(f"   ❌ 模型文档验证失败: {e}")
        return {"error": str(e)}

def validate_service_docs():
    """验证服务文档"""
    try:
        from app.services.unified_approval_service import UnifiedApprovalService

        service_docs = {}

        # 检查服务类文档
        class_docstring = UnifiedApprovalService.__doc__
        service_docs["class"] = {
            "has_docstring": bool(class_docstring and class_docstring.strip()),
            "docstring_length": len(class_docstring.strip()) if class_docstring else 0
        }

        if class_docstring and class_docstring.strip():
            print(f"      ✅ UnifiedApprovalService: 有类文档")
        else:
            print(f"      ⚠️ UnifiedApprovalService: 缺少类文档")

        # 检查方法文档
        methods = ['submit_approval', 'approve', 'reject']
        method_docs = {}

        for method_name in methods:
            if hasattr(UnifiedApprovalService, method_name):
                method = getattr(UnifiedApprovalService, method_name)
                docstring = method.__doc__

                method_docs[method_name] = {
                    "has_docstring": bool(docstring and docstring.strip()),
                    "docstring_length": len(docstring.strip()) if docstring else 0,
                    "signature": str(inspect.signature(method)) if hasattr(inspect, 'signature') else 'unknown'
                }

                if docstring and docstring.strip():
                    print(f"      ✅ {method_name}: 有方法文档")
                else:
                    print(f"      ⚠️ {method_name}: 缺少方法文档")
            else:
                print(f"      ❌ {method_name}: 方法不存在")
                method_docs[method_name] = {"exists": False}

        service_docs["methods"] = method_docs
        return service_docs

    except Exception as e:
        print(f"   ❌ 服务文档验证失败: {e}")
        return {"error": str(e)}

def validate_openapi_schema():
    """验证OpenAPI架构"""
    try:
        from app.main import app

        # 获取OpenAPI架构
        openapi_schema = app.openapi()

        schema_info = {
            "has_schema": bool(openapi_schema),
            "title": openapi_schema.get("info", {}).get("title", ""),
            "version": openapi_schema.get("info", {}).get("version", ""),
            "paths_count": len(openapi_schema.get("paths", {})),
            "components_count": len(openapi_schema.get("components", {}))
        }

        # 检查统一审批相关路径
        paths = openapi_schema.get("paths", {})
        approval_paths = [path for path in paths.keys() if "/approval/" in path]

        schema_info["approval_paths"] = approval_paths
        schema_info["approval_paths_count"] = len(approval_paths)

        print(f"      📊 OpenAPI架构信息:")
        print(f"         标题: {schema_info['title']}")
        print(f"         版本: {schema_info['version']}")
        print(f"         总路径数: {schema_info['paths_count']}")
        print(f"         审批路径数: {schema_info['approval_paths_count']}")

        if approval_paths:
            print(f"      ✅ 发现统一审批路径:")
            for path in approval_paths:
                print(f"         - {path}")
        else:
            print(f"      ❌ 未发现统一审批路径")

        return schema_info

    except Exception as e:
        print(f"   ❌ OpenAPI架构验证失败: {e}")
        return {"error": str(e)}

def generate_documentation_report(results):
    """生成文档验证报告"""
    print("\n" + "="*80)
    print("📊 API文档验证报告")
    print("="*80)

    # 统计得分
    scores = {}

    # 端点文档得分
    endpoint_docs = results.get("endpoint_documentation", {})
    if isinstance(endpoint_docs, dict) and "error" not in endpoint_docs:
        total_endpoints = len(endpoint_docs)
        documented_endpoints = sum(1 for doc in endpoint_docs.values() if doc.get("has_docstring", False))
        scores["endpoints"] = (documented_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
    else:
        scores["endpoints"] = 0

    # 模型文档得分
    model_docs = results.get("model_documentation", {})
    if isinstance(model_docs, dict) and "error" not in model_docs:
        total_models = len(model_docs)
        documented_models = sum(1 for doc in model_docs.values() if doc.get("has_docstring", False))
        scores["models"] = (documented_models / total_models * 100) if total_models > 0 else 0
    else:
        scores["models"] = 0

    # 服务文档得分
    service_docs = results.get("service_documentation", {})
    if isinstance(service_docs, dict) and "error" not in service_docs:
        service_score = 0
        if service_docs.get("class", {}).get("has_docstring", False):
            service_score += 25

        method_docs = service_docs.get("methods", {})
        documented_methods = sum(1 for doc in method_docs.values() if doc.get("has_docstring", False))
        total_methods = len(method_docs)
        if total_methods > 0:
            service_score += (documented_methods / total_methods) * 75

        scores["service"] = service_score
    else:
        scores["service"] = 0

    # OpenAPI得分
    openapi_info = results.get("openapi_schema", {})
    if isinstance(openapi_info, dict) and "error" not in openapi_info:
        openapi_score = 0
        if openapi_info.get("has_schema", False):
            openapi_score += 50
        if openapi_info.get("approval_paths_count", 0) > 0:
            openapi_score += 50
        scores["openapi"] = openapi_score
    else:
        scores["openapi"] = 0

    # 总体得分
    overall_score = sum(scores.values()) / len(scores)

    print(f"📈 文档质量得分:")
    print(f"   📡 API端点文档: {scores['endpoints']:.1f}/100")
    print(f"   📋 数据模型文档: {scores['models']:.1f}/100")
    print(f"   🔧 服务文档: {scores['service']:.1f}/100")
    print(f"   📚 OpenAPI架构: {scores['openapi']:.1f}/100")
    print(f"   🎯 总体得分: {overall_score:.1f}/100")

    if overall_score >= 90:
        quality_level = "优秀"
        print("🎉 API文档质量优秀！")
    elif overall_score >= 70:
        quality_level = "良好"
        print("✅ API文档质量良好")
    elif overall_score >= 50:
        quality_level = "一般"
        print("⚠️ API文档质量一般，建议改进")
    else:
        quality_level = "较差"
        print("🚨 API文档质量较差，需要大幅改进")

    # 保存报告
    report = {
        "validation_time": datetime.now().isoformat(),
        "validation_type": "api_documentation_validation",
        "results": results,
        "scores": scores,
        "summary": {
            "overall_score": overall_score,
            "quality_level": quality_level,
            "total_endpoints": len(endpoint_docs) if isinstance(endpoint_docs, dict) and "error" not in endpoint_docs else 0,
            "total_models": len(model_docs) if isinstance(model_docs, dict) and "error" not in model_docs else 0
        },
        "recommendations": [
            "确保所有API端点都有完整的docstring文档",
            "为所有Pydantic模型添加类文档",
            "为统一审批服务的所有方法添加详细文档",
            "定期更新OpenAPI架构以反映最新的API变化"
        ]
    }

    report_file = f"step6_api_documentation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 文档验证报告已保存: {report_file}")

    return report

if __name__ == "__main__":
    print("🚀 Step 6.3: 统一审批系统API文档验证")
    print("="*80)

    results = validate_api_documentation()
    report = generate_documentation_report(results)

    print("\n✅ API文档验证完成")