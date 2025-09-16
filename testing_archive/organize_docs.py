#!/usr/bin/env python3
"""
文档整理脚本 - 重新组织项目文档结构
"""

import os
import shutil
import glob
from pathlib import Path

def organize_documentation():
    """重新组织文档结构"""
    print("📚 开始整理项目文档结构...")

    # 创建文档目录结构
    doc_structure = {
        "docs": {
            "reports": "项目完成报告和里程碑",
            "guides": "用户指南和操作手册",
            "api": "API文档和接口说明",
            "testing": "测试报告和验证文档",
            "project": "项目规划和时间线",
            "security": "安全相关文档",
            "deployment": "部署和运维文档"
        }
    }

    # 创建目录结构
    for main_dir, subdirs in doc_structure.items():
        if isinstance(subdirs, dict):
            for subdir, description in subdirs.items():
                dir_path = f"{main_dir}/{subdir}"
                os.makedirs(dir_path, exist_ok=True)
                print(f"   📁 创建目录: {dir_path} - {description}")

    # 文档分类映射
    doc_mapping = {
        # 项目报告
        "docs/reports": [
            "*STEP*_COMPLETION_REPORT.md",
            "*STEP*_REPORT.md",
            "STEP5_COMPLETION_REPORT.md",
            "*FINAL_COMPLETION_REPORT.md"
        ],

        # 用户指南
        "docs/guides": [
            "*USER_GUIDE.md",
            "*USAGE*.md",
            "WECOM_APPROVAL_USAGE.md"
        ],

        # API文档
        "docs/api": [
            "*API*.md",
            "backend/docs/API*.md"
        ],

        # 测试文档
        "docs/testing": [
            "*test_report*.json",
            "*testing*.md",
            "step6_*_report_*.json",
            "backend/step6_*_report_*.json"
        ],

        # 项目文档
        "docs/project": [
            "*TIMELINE*.md",
            "*IMPLEMENTATION_PLAN*.md",
            "*PROJECT*.md",
            "CLAUDE_WORKFLOW.md"
        ],

        # 安全文档
        "docs/security": [
            "*SECURITY*.md",
            "PRODUCTION_SECURITY_SUMMARY.md"
        ],

        # 部署文档
        "docs/deployment": [
            "*CALLBACK*.md",
            "WECOM_CALLBACK_*.md"
        ]
    }

    # 执行文档移动
    moved_files = []
    for target_dir, patterns in doc_mapping.items():
        print(f"\n📂 整理到目录: {target_dir}")

        for pattern in patterns:
            # 查找匹配的文件
            files = glob.glob(pattern, recursive=True)
            files.extend(glob.glob(f"backend/{pattern}", recursive=True))
            files.extend(glob.glob(f"frontend/{pattern}", recursive=True))

            for file_path in files:
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    target_path = f"{target_dir}/{filename}"

                    try:
                        # 确保目标目录存在
                        os.makedirs(target_dir, exist_ok=True)

                        # 移动文件
                        shutil.copy2(file_path, target_path)
                        print(f"   📄 移动: {file_path} -> {target_path}")
                        moved_files.append((file_path, target_path))

                    except Exception as e:
                        print(f"   ❌ 移动失败: {file_path} - {e}")

    # 创建文档索引
    create_documentation_index(moved_files)

    print(f"\n✅ 文档整理完成！移动了 {len(moved_files)} 个文件")
    return moved_files

def create_documentation_index(moved_files):
    """创建文档索引"""
    index_content = """# 芯片报价系统文档索引

## 📚 文档结构说明

本项目的文档按照以下结构组织：

### 📊 reports/ - 项目报告
- Step完成报告
- 里程碑记录
- 项目交付报告

### 📖 guides/ - 用户指南
- 用户操作手册
- 系统使用指南
- 功能说明文档

### 🔌 api/ - API文档
- 接口文档
- API使用指南
- 开发者文档

### 🧪 testing/ - 测试文档
- 测试报告
- 验证文档
- 质量评估报告

### 📋 project/ - 项目文档
- 项目规划
- 实施计划
- 时间线记录

### 🔒 security/ - 安全文档
- 安全配置
- 生产环境安全总结

### 🚀 deployment/ - 部署文档
- 部署指南
- 运维文档
- 回调配置

## 📁 文档清单

"""

    # 按目录分组显示文件
    from collections import defaultdict
    files_by_dir = defaultdict(list)

    for original, target in moved_files:
        dir_name = os.path.dirname(target)
        filename = os.path.basename(target)
        files_by_dir[dir_name].append(filename)

    for dir_name in sorted(files_by_dir.keys()):
        dir_display = dir_name.replace("docs/", "")
        index_content += f"\n### {dir_display}/\n"
        for filename in sorted(files_by_dir[dir_name]):
            index_content += f"- {filename}\n"

    index_content += """
## 🔍 快速查找

### 想了解系统如何使用？
👉 查看 `guides/` 目录下的用户指南

### 需要查看项目进度？
👉 查看 `reports/` 目录下的完成报告

### 要进行API开发？
👉 查看 `api/` 目录下的接口文档

### 需要了解测试情况？
👉 查看 `testing/` 目录下的测试报告

### 要部署到生产环境？
👉 查看 `deployment/` 和 `security/` 目录

---

**文档生成时间**: """ + str(os.popen('date').read().strip()) + """
**项目**: 芯片报价系统统一审批模块
**版本**: v1.0
"""

    # 保存文档索引
    with open("docs/README.md", "w", encoding="utf-8") as f:
        f.write(index_content)

    print("   📋 创建文档索引: docs/README.md")

if __name__ == "__main__":
    organize_documentation()