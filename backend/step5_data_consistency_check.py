#!/usr/bin/env python3
"""
Step 5.1: 数据一致性检查脚本
检查数据库中审批相关数据的一致性问题，生成详细报告但不做任何修改

安全原则：
- 只读操作，不修改任何数据
- 生成详细报告用于分析
- 识别需要修复的数据不一致性

检查项目：
1. status 和 approval_status 字段一致性
2. ApprovalRecord 记录格式规范性
3. 缺失的 approval_method 字段
4. 重复的审批记录
5. 数据完整性验证
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Quote, ApprovalRecord
import json


class DataConsistencyChecker:
    def __init__(self):
        """初始化数据一致性检查器"""
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()
        self.report = {
            "check_time": datetime.now().isoformat(),
            "summary": {},
            "issues": {
                "status_inconsistencies": [],
                "missing_approval_methods": [],
                "invalid_approval_records": [],
                "duplicate_records": [],
                "data_integrity_issues": []
            },
            "statistics": {}
        }

    def check_status_field_consistency(self):
        """检查 status 和 approval_status 字段一致性"""
        print("🔍 检查 status 和 approval_status 字段一致性...")

        try:
            # 查询所有报价单的状态字段
            query = text("""
                SELECT
                    id, quote_number, status, approval_status,
                    created_at, updated_at
                FROM quotes
                WHERE is_deleted = 0
                ORDER BY created_at DESC
            """)

            result = self.db.execute(query)
            rows = result.fetchall()

            inconsistent_quotes = []
            total_quotes = 0

            # 定义状态映射规则
            status_mapping = {
                'draft': 'not_submitted',
                'pending': 'pending',
                'approved': 'approved',
                'rejected': 'rejected'
            }

            for row in rows:
                total_quotes += 1
                quote_id, quote_number, status, approval_status, created_at, updated_at = row

                # 检查状态一致性
                expected_approval_status = status_mapping.get(status)
                if expected_approval_status and approval_status != expected_approval_status:
                    inconsistent_quotes.append({
                        "quote_id": quote_id,
                        "quote_number": quote_number,
                        "current_status": status,
                        "current_approval_status": approval_status,
                        "expected_approval_status": expected_approval_status,
                        "created_at": str(created_at),
                        "updated_at": str(updated_at)
                    })

            self.report["issues"]["status_inconsistencies"] = inconsistent_quotes
            self.report["statistics"]["total_quotes"] = total_quotes
            self.report["statistics"]["inconsistent_quotes"] = len(inconsistent_quotes)

            print(f"   📊 总报价单数量: {total_quotes}")
            print(f"   ⚠️ 状态不一致数量: {len(inconsistent_quotes)}")

            if inconsistent_quotes:
                print("   🔸 不一致的报价单:")
                for issue in inconsistent_quotes[:5]:  # 只显示前5个
                    print(f"      - {issue['quote_number']}: {issue['current_status']} ≠ {issue['current_approval_status']}")

                if len(inconsistent_quotes) > 5:
                    print(f"      ... 还有 {len(inconsistent_quotes) - 5} 个")

        except Exception as e:
            print(f"   ❌ 检查状态一致性时出错: {e}")
            self.report["issues"]["status_inconsistencies"].append({
                "error": str(e),
                "check": "status_field_consistency"
            })

    def check_missing_approval_methods(self):
        """检查缺失的 approval_method 字段"""
        print("🔍 检查缺失的 approval_method 字段...")

        try:
            # 查询没有 approval_method 或为 NULL 的记录
            query = text("""
                SELECT
                    id, quote_number, approval_status, wecom_approval_id,
                    created_at, updated_at
                FROM quotes
                WHERE is_deleted = 0
                  AND (approval_method IS NULL OR approval_method = '')
                ORDER BY created_at DESC
            """)

            result = self.db.execute(query)
            rows = result.fetchall()

            missing_method_quotes = []

            for row in rows:
                quote_id, quote_number, approval_status, wecom_approval_id, created_at, updated_at = row

                # 推断审批方式
                inferred_method = "wecom" if wecom_approval_id else "internal"

                missing_method_quotes.append({
                    "quote_id": quote_id,
                    "quote_number": quote_number,
                    "approval_status": approval_status,
                    "wecom_approval_id": wecom_approval_id,
                    "inferred_method": inferred_method,
                    "created_at": str(created_at),
                    "updated_at": str(updated_at)
                })

            self.report["issues"]["missing_approval_methods"] = missing_method_quotes
            self.report["statistics"]["missing_approval_methods"] = len(missing_method_quotes)

            print(f"   📊 缺失 approval_method 的报价单: {len(missing_method_quotes)}")

            if missing_method_quotes:
                wecom_count = len([q for q in missing_method_quotes if q["inferred_method"] == "wecom"])
                internal_count = len([q for q in missing_method_quotes if q["inferred_method"] == "internal"])
                print(f"      - 推断为企业微信审批: {wecom_count}")
                print(f"      - 推断为内部审批: {internal_count}")

        except Exception as e:
            print(f"   ❌ 检查 approval_method 时出错: {e}")
            self.report["issues"]["missing_approval_methods"].append({
                "error": str(e),
                "check": "missing_approval_methods"
            })

    def check_approval_records_format(self):
        """检查 ApprovalRecord 记录格式规范性"""
        print("🔍 检查 ApprovalRecord 记录格式规范性...")

        try:
            # 查询所有审批记录
            query = text("""
                SELECT
                    id, quote_id, action, approver_id, comments, created_at
                FROM approval_records
                ORDER BY created_at DESC
            """)

            result = self.db.execute(query)
            rows = result.fetchall()

            invalid_records = []
            total_records = len(rows)

            for row in rows:
                record_id, quote_id, action, approver_id, comments, created_at = row

                issues = []

                # 检查必要字段
                if not action:
                    issues.append("缺少 action 字段")

                if not approver_id:
                    issues.append("缺少 approver_id 字段")

                # 检查 action 值有效性
                valid_actions = ['submit', 'approve', 'reject', 'cancel', 'update']
                if action and action not in valid_actions:
                    issues.append(f"无效的 action 值: {action}")

                if issues:
                    invalid_records.append({
                        "record_id": record_id,
                        "quote_id": quote_id,
                        "action": action,
                        "approver_id": approver_id,
                        "issues": issues,
                        "created_at": str(created_at)
                    })

            self.report["issues"]["invalid_approval_records"] = invalid_records
            self.report["statistics"]["total_approval_records"] = total_records
            self.report["statistics"]["invalid_approval_records"] = len(invalid_records)

            print(f"   📊 总审批记录数量: {total_records}")
            print(f"   ⚠️ 格式异常记录数量: {len(invalid_records)}")

            if invalid_records:
                print("   🔸 格式异常的记录:")
                for record in invalid_records[:3]:  # 只显示前3个
                    print(f"      - 记录 {record['record_id']}: {', '.join(record['issues'])}")

        except Exception as e:
            print(f"   ❌ 检查审批记录格式时出错: {e}")
            self.report["issues"]["invalid_approval_records"].append({
                "error": str(e),
                "check": "approval_records_format"
            })

    def check_duplicate_approval_records(self):
        """检查重复的审批记录"""
        print("🔍 检查重复的审批记录...")

        try:
            # 查找相同 quote_id, action, approver_id 的重复记录
            query = text("""
                SELECT
                    quote_id, action, approver_id, COUNT(*) as count,
                    MIN(id) as first_id, MAX(id) as last_id,
                    MIN(created_at) as first_created, MAX(created_at) as last_created
                FROM approval_records
                GROUP BY quote_id, action, approver_id
                HAVING COUNT(*) > 1
                ORDER BY count DESC, quote_id
            """)

            result = self.db.execute(query)
            rows = result.fetchall()

            duplicate_groups = []

            for row in rows:
                quote_id, action, approver_id, count, first_id, last_id, first_created, last_created = row

                # 获取这组重复记录的详细信息
                detail_query = text("""
                    SELECT id, comments, created_at
                    FROM approval_records
                    WHERE quote_id = :quote_id AND action = :action AND approver_id = :approver_id
                    ORDER BY created_at
                """)

                detail_result = self.db.execute(detail_query, {
                    "quote_id": quote_id,
                    "action": action,
                    "approver_id": approver_id
                })
                detail_rows = detail_result.fetchall()

                records = []
                for detail_row in detail_rows:
                    records.append({
                        "id": detail_row[0],
                        "comments": detail_row[1],
                        "created_at": str(detail_row[2])
                    })

                duplicate_groups.append({
                    "quote_id": quote_id,
                    "action": action,
                    "approver_id": approver_id,
                    "count": count,
                    "time_span": str(last_created - first_created) if first_created != last_created else "同时创建",
                    "records": records
                })

            self.report["issues"]["duplicate_records"] = duplicate_groups
            self.report["statistics"]["duplicate_groups"] = len(duplicate_groups)
            self.report["statistics"]["total_duplicate_records"] = sum(group["count"] for group in duplicate_groups)

            print(f"   📊 重复记录组数量: {len(duplicate_groups)}")
            if duplicate_groups:
                total_duplicates = sum(group["count"] for group in duplicate_groups)
                print(f"   📊 总重复记录数量: {total_duplicates}")
                print("   🔸 重复记录组:")
                for group in duplicate_groups[:3]:  # 只显示前3组
                    print(f"      - 报价单 {group['quote_id']}, 操作 {group['action']}: {group['count']} 条记录")

        except Exception as e:
            print(f"   ❌ 检查重复记录时出错: {e}")
            self.report["issues"]["duplicate_records"].append({
                "error": str(e),
                "check": "duplicate_approval_records"
            })

    def check_data_integrity(self):
        """检查数据完整性"""
        print("🔍 检查数据完整性...")

        try:
            integrity_issues = []

            # 检查1: 报价单是否有对应的用户
            query1 = text("""
                SELECT q.id, q.quote_number, q.created_by
                FROM quotes q
                LEFT JOIN users u ON q.created_by = u.id
                WHERE q.is_deleted = 0 AND u.id IS NULL
            """)

            result1 = self.db.execute(query1)
            orphan_quotes = result1.fetchall()

            if orphan_quotes:
                integrity_issues.append({
                    "type": "orphan_quotes",
                    "description": "报价单创建者不存在",
                    "count": len(orphan_quotes),
                    "examples": [{"quote_id": row[0], "quote_number": row[1], "user_id": row[2]}
                               for row in orphan_quotes[:3]]
                })

            # 检查2: 审批记录是否有对应的报价单
            query2 = text("""
                SELECT ar.id, ar.quote_id, ar.action
                FROM approval_records ar
                LEFT JOIN quotes q ON ar.quote_id = q.id
                WHERE q.id IS NULL
            """)

            result2 = self.db.execute(query2)
            orphan_records = result2.fetchall()

            if orphan_records:
                integrity_issues.append({
                    "type": "orphan_approval_records",
                    "description": "审批记录对应的报价单不存在",
                    "count": len(orphan_records),
                    "examples": [{"record_id": row[0], "quote_id": row[1], "action": row[2]}
                               for row in orphan_records[:3]]
                })

            # 检查3: 企业微信审批ID的一致性
            query3 = text("""
                SELECT id, quote_number, wecom_approval_id
                FROM quotes
                WHERE is_deleted = 0
                  AND wecom_approval_id IS NOT NULL
                  AND wecom_approval_id != ''
                  AND approval_method != 'wecom'
            """)

            result3 = self.db.execute(query3)
            wecom_inconsistent = result3.fetchall()

            if wecom_inconsistent:
                integrity_issues.append({
                    "type": "wecom_method_inconsistent",
                    "description": "有企业微信审批ID但approval_method不是wecom",
                    "count": len(wecom_inconsistent),
                    "examples": [{"quote_id": row[0], "quote_number": row[1], "wecom_id": row[2]}
                               for row in wecom_inconsistent[:3]]
                })

            self.report["issues"]["data_integrity_issues"] = integrity_issues
            self.report["statistics"]["integrity_issue_types"] = len(integrity_issues)

            print(f"   📊 数据完整性问题类型: {len(integrity_issues)}")

            for issue in integrity_issues:
                print(f"   ⚠️ {issue['description']}: {issue['count']} 条记录")

        except Exception as e:
            print(f"   ❌ 检查数据完整性时出错: {e}")
            self.report["issues"]["data_integrity_issues"].append({
                "error": str(e),
                "check": "data_integrity"
            })

    def generate_summary(self):
        """生成检查总结"""
        print("📋 生成检查总结...")

        stats = self.report["statistics"]
        issues = self.report["issues"]

        total_issues = (
            len(issues["status_inconsistencies"]) +
            len(issues["missing_approval_methods"]) +
            len(issues["invalid_approval_records"]) +
            len(issues["duplicate_records"]) +
            len(issues["data_integrity_issues"])
        )

        summary = {
            "total_quotes": stats.get("total_quotes", 0),
            "total_approval_records": stats.get("total_approval_records", 0),
            "total_issues_found": total_issues,
            "critical_issues": len(issues["status_inconsistencies"]) + len(issues["data_integrity_issues"]),
            "data_quality_score": 0,
            "recommended_actions": []
        }

        # 计算数据质量分数 (0-100)
        if stats.get("total_quotes", 0) > 0:
            quality_score = max(0, 100 - (total_issues * 10))
            summary["data_quality_score"] = min(100, quality_score)

        # 推荐修复操作
        if issues["status_inconsistencies"]:
            summary["recommended_actions"].append("修复状态字段不一致性")

        if issues["missing_approval_methods"]:
            summary["recommended_actions"].append("补充缺失的审批方式标识")

        if issues["invalid_approval_records"]:
            summary["recommended_actions"].append("标准化审批记录格式")

        if issues["duplicate_records"]:
            summary["recommended_actions"].append("清理重复的审批记录")

        if issues["data_integrity_issues"]:
            summary["recommended_actions"].append("修复数据完整性问题")

        self.report["summary"] = summary

    def save_report(self, filename: Optional[str] = None):
        """保存检查报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_consistency_report_{timestamp}.json"

        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, ensure_ascii=False, indent=2)

            print(f"📄 检查报告已保存: {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return None

    def print_summary_report(self):
        """打印检查总结报告"""
        print("\n" + "=" * 80)
        print("📊 数据一致性检查报告总结")
        print("=" * 80)

        summary = self.report["summary"]

        print(f"🔍 检查时间: {self.report['check_time']}")
        print(f"📈 数据质量分数: {summary['data_quality_score']}/100")
        print(f"📊 总报价单数量: {summary['total_quotes']}")
        print(f"📊 总审批记录数量: {summary['total_approval_records']}")
        print(f"⚠️ 发现问题总数: {summary['total_issues_found']}")
        print(f"🚨 关键问题数量: {summary['critical_issues']}")

        print("\n🔍 具体问题分布:")
        issues = self.report["issues"]
        print(f"   - 状态不一致: {len(issues['status_inconsistencies'])} 个")
        print(f"   - 缺失审批方式: {len(issues['missing_approval_methods'])} 个")
        print(f"   - 记录格式异常: {len(issues['invalid_approval_records'])} 个")
        print(f"   - 重复记录: {len(issues['duplicate_records'])} 组")
        print(f"   - 数据完整性: {len(issues['data_integrity_issues'])} 类")

        if summary["recommended_actions"]:
            print("\n🛠️ 推荐修复操作:")
            for i, action in enumerate(summary["recommended_actions"], 1):
                print(f"   {i}. {action}")

        print("\n" + "=" * 80)

    def run_full_check(self):
        """运行完整的数据一致性检查"""
        print("🚀 开始数据一致性检查...")
        print("⚠️ 注意：此检查只读取数据，不会做任何修改")
        print()

        try:
            # 执行各项检查
            self.check_status_field_consistency()
            print()

            self.check_missing_approval_methods()
            print()

            self.check_approval_records_format()
            print()

            self.check_duplicate_approval_records()
            print()

            self.check_data_integrity()
            print()

            # 生成总结
            self.generate_summary()

            # 保存报告
            report_file = self.save_report()

            # 打印总结
            self.print_summary_report()

            return True, report_file

        except Exception as e:
            print(f"❌ 数据一致性检查失败: {e}")
            return False, None

        finally:
            self.db.close()


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 Step 5.1: 数据一致性检查")
    print("=" * 80)
    print()

    checker = DataConsistencyChecker()
    success, report_file = checker.run_full_check()

    if success:
        print("✅ 数据一致性检查完成")
        if report_file:
            print(f"📄 详细报告文件: {report_file}")
        return 0
    else:
        print("❌ 数据一致性检查失败")
        return 1


if __name__ == "__main__":
    exit(main())