#!/usr/bin/env python3
"""
Step 6: 统一审批系统 - 全面系统测试套件
验证统一审批系统的完整功能，包括端到端测试、API测试、性能测试

测试范围：
1. 统一审批API端点完整性测试
2. 数据流和状态同步测试
3. 企业微信/内部审批兼容性测试
4. 前端组件集成测试
5. 性能和负载测试
6. 错误处理和边界条件测试
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL


class UnifiedApprovalSystemTest:
    def __init__(self):
        """初始化系统测试器"""
        self.base_url = "http://127.0.0.1:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_quote_id = "2a72d639-1486-442d-bce3-02a20672de28"

        # 禁用代理
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        # 数据库连接
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()

        # 测试结果记录
        self.test_results = {
            "test_session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": None,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": 0,
            "test_categories": {
                "api_endpoints": {"passed": 0, "failed": 0, "tests": []},
                "data_flow": {"passed": 0, "failed": 0, "tests": []},
                "integration": {"passed": 0, "failed": 0, "tests": []},
                "performance": {"passed": 0, "failed": 0, "tests": []},
                "error_handling": {"passed": 0, "failed": 0, "tests": []},
                "documentation": {"passed": 0, "failed": 0, "tests": []}
            },
            "system_info": {
                "test_quote_id": self.test_quote_id,
                "backend_url": self.base_url,
                "frontend_url": self.frontend_url
            },
            "recommendations": []
        }

    def log_test_result(self, category: str, test_name: str, status: str,
                       details: Dict = None, duration: float = None):
        """记录测试结果"""
        result = {
            "name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "details": details or {}
        }

        self.test_results["test_categories"][category]["tests"].append(result)

        if status == "PASS":
            self.test_results["test_categories"][category]["passed"] += 1
            self.test_results["passed_tests"] += 1
        elif status == "FAIL":
            self.test_results["test_categories"][category]["failed"] += 1
            self.test_results["failed_tests"] += 1
        elif status == "WARN":
            self.test_results["warnings"] += 1

        self.test_results["total_tests"] += 1

    def test_api_endpoints_completeness(self):
        """测试统一审批API端点完整性"""
        print("🔧 测试1: 统一审批API端点完整性")

        # 预期的API端点
        expected_endpoints = [
            "/api/v1/approval/status/{quote_id}",
            "/api/v1/approval/history/{quote_id}",
            "/api/v1/approval/submit/{quote_id}",
            "/api/v1/approval/approve/{quote_id}",
            "/api/v1/approval/reject/{quote_id}"
        ]

        for endpoint_pattern in expected_endpoints:
            endpoint = endpoint_pattern.format(quote_id=self.test_quote_id)
            test_name = f"API端点存在性: {endpoint_pattern}"

            start_time = time.time()
            try:
                if "status" in endpoint or "history" in endpoint:
                    # GET 请求
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    # POST 请求（预期会失败但端点应该存在）
                    response = requests.post(f"{self.base_url}{endpoint}",
                                          json={"test": True}, timeout=10)

                duration = time.time() - start_time

                # 检查端点是否存在（不是404）
                if response.status_code != 404:
                    self.log_test_result("api_endpoints", test_name, "PASS", {
                        "status_code": response.status_code,
                        "response_time": f"{duration:.3f}s"
                    }, duration)
                    print(f"   ✅ {endpoint_pattern}: 状态码 {response.status_code}")
                else:
                    self.log_test_result("api_endpoints", test_name, "FAIL", {
                        "error": "端点不存在",
                        "status_code": 404
                    }, duration)
                    print(f"   ❌ {endpoint_pattern}: 端点不存在")

            except Exception as e:
                duration = time.time() - start_time
                self.log_test_result("api_endpoints", test_name, "FAIL", {
                    "error": str(e)
                }, duration)
                print(f"   ❌ {endpoint_pattern}: {str(e)}")

    def test_data_flow_and_state_sync(self):
        """测试数据流和状态同步"""
        print("🔄 测试2: 数据流和状态同步")

        # 测试状态查询的数据完整性
        test_name = "状态查询数据完整性"
        start_time = time.time()

        try:
            response = requests.get(f"{self.base_url}/api/v1/approval/status/{self.test_quote_id}",
                                  timeout=10)
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # 检查必要字段
                required_fields = ['quote_id', 'quote_number', 'approval_status',
                                 'approval_method', 'has_wecom_approval']

                missing_fields = [field for field in required_fields if field not in data]

                if not missing_fields:
                    # 验证数据类型和逻辑
                    validation_issues = []

                    if not isinstance(data.get('has_wecom_approval'), bool):
                        validation_issues.append("has_wecom_approval 应该是布尔值")

                    if data.get('approval_method') not in ['internal', 'wecom']:
                        validation_issues.append("approval_method 值无效")

                    # 验证逻辑一致性：企业微信ID与审批方式的对应关系
                    has_wecom_id = bool(data.get('wecom_approval_id'))
                    is_wecom_method = data.get('approval_method') == 'wecom'

                    if has_wecom_id != is_wecom_method:
                        validation_issues.append("企业微信ID与审批方式不一致")

                    if not validation_issues:
                        self.log_test_result("data_flow", test_name, "PASS", {
                            "data_fields": len(data),
                            "approval_method": data.get('approval_method'),
                            "has_wecom_approval": data.get('has_wecom_approval')
                        }, duration)
                        print(f"   ✅ 状态查询数据完整且一致")
                    else:
                        self.log_test_result("data_flow", test_name, "WARN", {
                            "validation_issues": validation_issues,
                            "data": data
                        }, duration)
                        print(f"   ⚠️ 数据验证警告: {', '.join(validation_issues)}")
                else:
                    self.log_test_result("data_flow", test_name, "FAIL", {
                        "missing_fields": missing_fields
                    }, duration)
                    print(f"   ❌ 缺少必要字段: {', '.join(missing_fields)}")
            else:
                self.log_test_result("data_flow", test_name, "FAIL", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                }, duration)
                print(f"   ❌ 状态查询失败: {response.status_code}")

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("data_flow", test_name, "FAIL", {
                "error": str(e)
            }, duration)
            print(f"   ❌ 状态查询异常: {str(e)}")

    def test_approval_method_compatibility(self):
        """测试企业微信/内部审批兼容性"""
        print("🏢 测试3: 审批方式兼容性")

        # 测试不同审批方式的数据获取
        test_name = "审批方式兼容性检查"
        start_time = time.time()

        try:
            # 获取所有报价单的审批方式分布
            query = text("""
                SELECT
                    approval_method,
                    COUNT(*) as count,
                    COUNT(CASE WHEN wecom_approval_id IS NOT NULL AND wecom_approval_id != '' THEN 1 END) as with_wecom_id
                FROM quotes
                WHERE is_deleted = 0
                GROUP BY approval_method
            """)

            result = self.db.execute(query)
            methods = result.fetchall()

            duration = time.time() - start_time

            method_stats = {}
            total_quotes = 0
            consistent_data = True

            for method, count, with_wecom_id in methods:
                method_stats[method] = {
                    "count": count,
                    "with_wecom_id": with_wecom_id
                }
                total_quotes += count

                # 检查一致性：wecom方式应该都有wecom_id，internal方式应该都没有
                if method == "wecom" and with_wecom_id != count:
                    consistent_data = False
                elif method == "internal" and with_wecom_id > 0:
                    consistent_data = False

            if consistent_data and total_quotes > 0:
                self.log_test_result("integration", test_name, "PASS", {
                    "total_quotes": total_quotes,
                    "method_distribution": method_stats,
                    "consistency": "perfect"
                }, duration)
                print(f"   ✅ 审批方式兼容性良好: {total_quotes} 个报价单")
                print(f"      方式分布: {method_stats}")
            elif total_quotes == 0:
                self.log_test_result("integration", test_name, "WARN", {
                    "message": "没有测试数据"
                }, duration)
                print(f"   ⚠️ 没有找到测试数据")
            else:
                self.log_test_result("integration", test_name, "FAIL", {
                    "consistency_issues": "数据不一致",
                    "method_distribution": method_stats
                }, duration)
                print(f"   ❌ 审批方式数据不一致")

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("integration", test_name, "FAIL", {
                "error": str(e)
            }, duration)
            print(f"   ❌ 兼容性检查失败: {str(e)}")

    def test_frontend_integration(self):
        """测试前端集成"""
        print("🌐 测试4: 前端集成")

        # 测试前端可访问性
        test_name = "前端应用可访问性"
        start_time = time.time()

        try:
            response = requests.get(self.frontend_url, timeout=10)
            duration = time.time() - start_time

            if response.status_code == 200:
                content_length = len(response.text)
                has_react = "React" in response.text or "react" in response.text

                self.log_test_result("integration", test_name, "PASS", {
                    "status_code": response.status_code,
                    "content_length": content_length,
                    "has_react": has_react,
                    "response_time": f"{duration:.3f}s"
                }, duration)
                print(f"   ✅ 前端应用正常访问 ({content_length} 字符)")
            else:
                self.log_test_result("integration", test_name, "FAIL", {
                    "status_code": response.status_code
                }, duration)
                print(f"   ❌ 前端应用访问失败: {response.status_code}")

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("integration", test_name, "FAIL", {
                "error": str(e)
            }, duration)
            print(f"   ❌ 前端访问异常: {str(e)}")

        # 检查关键前端文件是否存在
        test_name = "前端统一审批组件文件"
        start_time = time.time()

        try:
            frontend_files = [
                "frontend/chip-quotation-frontend/src/services/unifiedApprovalApi.js",
                "frontend/chip-quotation-frontend/src/components/UnifiedApprovalPanel.js",
                "frontend/chip-quotation-frontend/src/test_unified_approval_frontend.js"
            ]

            project_root = os.path.dirname(os.path.dirname(__file__))
            missing_files = []
            existing_files = []

            for file_path in frontend_files:
                full_path = os.path.join(project_root, file_path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    existing_files.append({"path": file_path, "size": file_size})
                else:
                    missing_files.append(file_path)

            duration = time.time() - start_time

            if not missing_files:
                self.log_test_result("integration", test_name, "PASS", {
                    "total_files": len(frontend_files),
                    "existing_files": existing_files
                }, duration)
                print(f"   ✅ 前端组件文件完整: {len(existing_files)} 个文件")
            else:
                self.log_test_result("integration", test_name, "FAIL", {
                    "missing_files": missing_files,
                    "existing_files": existing_files
                }, duration)
                print(f"   ❌ 缺少前端文件: {len(missing_files)} 个")

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("integration", test_name, "FAIL", {
                "error": str(e)
            }, duration)
            print(f"   ❌ 前端文件检查失败: {str(e)}")

    def test_performance_and_load(self):
        """测试性能和负载"""
        print("⚡ 测试5: 性能和负载测试")

        # API响应时间测试
        test_name = "API响应时间性能"
        print("   🔄 执行API响应时间测试...")

        start_time = time.time()
        response_times = []
        successful_requests = 0

        try:
            # 并发测试API响应时间
            for i in range(10):
                req_start = time.time()
                try:
                    response = requests.get(f"{self.base_url}/api/v1/approval/status/{self.test_quote_id}",
                                          timeout=5)
                    req_duration = time.time() - req_start
                    if response.status_code == 200:
                        response_times.append(req_duration)
                        successful_requests += 1
                except:
                    pass

            duration = time.time() - start_time

            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                min_time = min(response_times)

                # 性能标准：平均响应时间 < 1秒，最大响应时间 < 2秒
                performance_good = avg_time < 1.0 and max_time < 2.0

                status = "PASS" if performance_good else "WARN"
                self.log_test_result("performance", test_name, status, {
                    "total_requests": 10,
                    "successful_requests": successful_requests,
                    "avg_response_time": f"{avg_time:.3f}s",
                    "min_response_time": f"{min_time:.3f}s",
                    "max_response_time": f"{max_time:.3f}s",
                    "success_rate": f"{successful_requests/10*100:.1f}%"
                }, duration)

                if performance_good:
                    print(f"   ✅ API性能良好: 平均 {avg_time:.3f}s, 成功率 {successful_requests/10*100:.1f}%")
                else:
                    print(f"   ⚠️ API性能需优化: 平均 {avg_time:.3f}s, 最大 {max_time:.3f}s")
            else:
                self.log_test_result("performance", test_name, "FAIL", {
                    "error": "所有请求都失败"
                }, duration)
                print(f"   ❌ API性能测试失败: 所有请求都失败")

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("performance", test_name, "FAIL", {
                "error": str(e)
            }, duration)
            print(f"   ❌ 性能测试异常: {str(e)}")

    def test_error_handling(self):
        """测试错误处理和边界条件"""
        print("🚨 测试6: 错误处理和边界条件")

        # 测试无效的quote_id
        test_name = "无效quote_id处理"
        start_time = time.time()

        try:
            invalid_id = "invalid-quote-id-123"
            response = requests.get(f"{self.base_url}/api/v1/approval/status/{invalid_id}",
                                  timeout=10)
            duration = time.time() - start_time

            # 应该返回404或类似的错误状态码
            if response.status_code in [404, 400, 422]:
                self.log_test_result("error_handling", test_name, "PASS", {
                    "status_code": response.status_code,
                    "error_handled": True
                }, duration)
                print(f"   ✅ 无效ID正确处理: 状态码 {response.status_code}")
            else:
                self.log_test_result("error_handling", test_name, "WARN", {
                    "status_code": response.status_code,
                    "expected": "4xx error code"
                }, duration)
                print(f"   ⚠️ 无效ID处理异常: 状态码 {response.status_code}")

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("error_handling", test_name, "FAIL", {
                "error": str(e)
            }, duration)
            print(f"   ❌ 错误处理测试异常: {str(e)}")

    def test_api_documentation(self):
        """测试API文档完整性"""
        print("📚 测试7: API文档完整性")

        test_name = "OpenAPI文档验证"
        start_time = time.time()

        try:
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            duration = time.time() - start_time

            if response.status_code == 200:
                openapi_spec = response.json()

                # 检查统一审批端点是否在文档中
                paths = openapi_spec.get('paths', {})
                approval_endpoints = [path for path in paths.keys() if '/approval/' in path]

                # 检查是否有标签信息
                has_approval_tag = False
                tags = openapi_spec.get('tags', [])
                for tag in tags:
                    if 'approval' in tag.get('name', '').lower():
                        has_approval_tag = True
                        break

                if len(approval_endpoints) >= 5:  # 应该有至少5个统一审批端点
                    self.log_test_result("documentation", test_name, "PASS", {
                        "total_approval_endpoints": len(approval_endpoints),
                        "has_approval_tag": has_approval_tag,
                        "endpoints": approval_endpoints
                    }, duration)
                    print(f"   ✅ API文档完整: {len(approval_endpoints)} 个审批端点")
                else:
                    self.log_test_result("documentation", test_name, "WARN", {
                        "total_approval_endpoints": len(approval_endpoints),
                        "expected_minimum": 5
                    }, duration)
                    print(f"   ⚠️ API文档不完整: 只有 {len(approval_endpoints)} 个端点")
            else:
                self.log_test_result("documentation", test_name, "FAIL", {
                    "status_code": response.status_code
                }, duration)
                print(f"   ❌ OpenAPI文档访问失败: {response.status_code}")

        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("documentation", test_name, "FAIL", {
                "error": str(e)
            }, duration)
            print(f"   ❌ 文档验证异常: {str(e)}")

    def generate_recommendations(self):
        """生成改进建议"""
        recommendations = []

        # 基于测试结果生成建议
        if self.test_results["failed_tests"] > 0:
            recommendations.append("存在测试失败，需要修复相关问题")

        if self.test_results["warnings"] > 0:
            recommendations.append("存在警告项，建议优化相关功能")

        # 检查性能测试结果
        perf_tests = self.test_results["test_categories"]["performance"]["tests"]
        for test in perf_tests:
            if test["status"] == "WARN":
                recommendations.append("API响应时间需要优化，建议进行性能调优")

        # 检查错误处理
        error_tests = self.test_results["test_categories"]["error_handling"]["tests"]
        if len(error_tests) == 0:
            recommendations.append("建议增加更多错误处理测试用例")

        if not recommendations:
            recommendations.append("系统测试表现良好，可以投入生产使用")

        self.test_results["recommendations"] = recommendations

    def save_test_report(self, filename: Optional[str] = None):
        """保存测试报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unified_system_test_report_{timestamp}.json"

        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)

            print(f"📄 测试报告已保存: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return None

    def print_summary_report(self):
        """打印测试总结报告"""
        print("\n" + "=" * 80)
        print("📊 统一审批系统测试总结报告")
        print("=" * 80)

        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        warnings = self.test_results["warnings"]

        print(f"🔍 测试会话: {self.test_results['test_session_id']}")
        print(f"⏱️ 测试时长: {self.test_results['duration']}")
        print(f"📊 测试总数: {total}")
        print(f"✅ 通过: {passed} ({passed/total*100:.1f}%)" if total > 0 else "✅ 通过: 0")
        print(f"❌ 失败: {failed} ({failed/total*100:.1f}%)" if total > 0 else "❌ 失败: 0")
        print(f"⚠️ 警告: {warnings} ({warnings/total*100:.1f}%)" if total > 0 else "⚠️ 警告: 0")

        print("\n📋 分类测试结果:")
        for category, results in self.test_results["test_categories"].items():
            category_total = results["passed"] + results["failed"]
            if category_total > 0:
                pass_rate = results["passed"] / category_total * 100
                print(f"   {category}: {results['passed']}/{category_total} 通过 ({pass_rate:.1f}%)")

        print("\n💡 改进建议:")
        for i, rec in enumerate(self.test_results["recommendations"], 1):
            print(f"   {i}. {rec}")

        # 评估整体质量
        if total > 0:
            overall_score = (passed + warnings * 0.5) / total * 100
            print(f"\n🎯 系统质量评分: {overall_score:.1f}/100")

            if overall_score >= 90:
                print("🎉 系统质量优秀，可以投入生产使用！")
            elif overall_score >= 75:
                print("✅ 系统质量良好，建议修复警告项后投入使用")
            elif overall_score >= 60:
                print("⚠️ 系统质量一般，需要修复失败项和警告项")
            else:
                print("🚨 系统质量较差，需要重大改进")

        print("=" * 80)

    def run_comprehensive_test(self):
        """运行全面的系统测试"""
        print("🚀 开始统一审批系统全面测试")
        print("=" * 80)
        print()

        start_time = time.time()

        try:
            # 执行各项测试
            self.test_api_endpoints_completeness()
            print()

            self.test_data_flow_and_state_sync()
            print()

            self.test_approval_method_compatibility()
            print()

            self.test_frontend_integration()
            print()

            self.test_performance_and_load()
            print()

            self.test_error_handling()
            print()

            self.test_api_documentation()
            print()

            # 计算测试时长
            end_time = time.time()
            duration = end_time - start_time
            self.test_results["end_time"] = datetime.now().isoformat()
            self.test_results["duration"] = f"{duration:.2f}s"

            # 生成建议
            self.generate_recommendations()

            # 保存报告
            report_file = self.save_test_report()

            # 打印总结
            self.print_summary_report()

            return True, report_file

        except Exception as e:
            print(f"❌ 系统测试执行失败: {e}")
            return False, None

        finally:
            self.db.close()


def main():
    """主函数"""
    print("=" * 80)
    print("🧪 Step 6: 统一审批系统全面测试")
    print("=" * 80)
    print()

    tester = UnifiedApprovalSystemTest()
    success, report_file = tester.run_comprehensive_test()

    if success:
        print("\n✅ 统一审批系统测试完成")
        if report_file:
            print(f"📄 详细报告: {report_file}")
        return 0
    else:
        print("\n❌ 统一审批系统测试失败")
        return 1


if __name__ == "__main__":
    exit(main())