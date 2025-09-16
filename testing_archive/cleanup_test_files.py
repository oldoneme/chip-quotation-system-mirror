#!/usr/bin/env python3
"""
测试文件清理脚本 - 统一管理和清理测试文件
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime

def cleanup_test_files():
    """清理和整理测试文件"""
    print("🧹 开始清理和整理测试文件...")

    # 创建测试文件存档目录
    archive_dir = "testing_archive"
    current_tests_dir = "backend/tests_current"

    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(current_tests_dir, exist_ok=True)

    print(f"   📁 创建存档目录: {archive_dir}")
    print(f"   📁 创建当前测试目录: {current_tests_dir}")

    # 定义测试文件模式
    test_patterns = {
        "step_tests": [
            "backend/test_step*.py",
            "backend/step*_test*.py",
            "test_step*.py",
            "step*_test*.py"
        ],
        "unified_tests": [
            "backend/test_unified*.py",
            "backend/unified_*test*.py",
            "test_unified*.py",
            "unified_*test*.py"
        ],
        "api_tests": [
            "backend/test_*api*.py",
            "backend/*api*_test*.py",
            "test_*api*.py",
            "*api*_test*.py"
        ],
        "wecom_tests": [
            "backend/test_wecom*.py",
            "backend/wecom_*test*.py",
            "test_wecom*.py",
            "wecom_*test*.py"
        ],
        "debug_tests": [
            "backend/test_*debug*.py",
            "backend/debug_*.py",
            "backend/comprehensive_*.py",
            "test_*debug*.py",
            "debug_*.py"
        ],
        "report_files": [
            "backend/*_report_*.json",
            "backend/data_consistency_report*.json",
            "backend/migration_log*.json",
            "*_report_*.json"
        ],
        "temp_files": [
            "backend/test.db",
            "backend/*.db-journal",
            "backend/temp_*.py",
            "temp_*.py"
        ]
    }

    # 当前需要保留的测试文件（正在使用的）
    keep_current = [
        "backend/step6_unified_system_test.py",
        "backend/step6_performance_test.py",
        "backend/step6_api_documentation_validator.py"
    ]

    moved_files = []
    kept_files = []

    # 处理每种类型的测试文件
    for category, patterns in test_patterns.items():
        print(f"\n📂 处理 {category} 类文件...")

        category_dir = f"{archive_dir}/{category}"
        os.makedirs(category_dir, exist_ok=True)

        for pattern in patterns:
            files = glob.glob(pattern, recursive=True)

            for file_path in files:
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)

                    # 检查是否需要保留
                    if file_path in keep_current:
                        # 复制到当前测试目录
                        target_path = f"{current_tests_dir}/{filename}"
                        shutil.copy2(file_path, target_path)
                        kept_files.append((file_path, target_path))
                        print(f"   📋 保留: {file_path} -> {target_path}")
                    else:
                        # 移动到存档目录
                        target_path = f"{category_dir}/{filename}"

                        # 如果文件已存在，添加时间戳
                        if os.path.exists(target_path):
                            name, ext = os.path.splitext(filename)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            target_path = f"{category_dir}/{name}_{timestamp}{ext}"

                        try:
                            shutil.move(file_path, target_path)
                            moved_files.append((file_path, target_path))
                            print(f"   🗂️ 归档: {file_path} -> {target_path}")
                        except Exception as e:
                            print(f"   ❌ 移动失败: {file_path} - {e}")

    # 创建清理总结报告
    create_cleanup_summary(moved_files, kept_files, archive_dir)

    print(f"\n✅ 测试文件整理完成！")
    print(f"   📦 归档文件: {len(moved_files)} 个")
    print(f"   📋 保留文件: {len(kept_files)} 个")
    print(f"   📁 存档位置: {archive_dir}/")
    print(f"   📁 当前测试: {current_tests_dir}/")

    return moved_files, kept_files

def create_cleanup_summary(moved_files, kept_files, archive_dir):
    """创建清理总结报告"""
    summary_content = f"""# 测试文件清理总结报告

**清理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**清理目的**: 统一管理测试文件，为项目完成做准备

## 📊 清理统计

- **归档文件数量**: {len(moved_files)}
- **保留文件数量**: {len(kept_files)}
- **存档位置**: `{archive_dir}/`
- **当前测试位置**: `backend/tests_current/`

## 📦 归档文件列表

"""

    # 按类别分组显示归档文件
    from collections import defaultdict
    files_by_category = defaultdict(list)

    for original, target in moved_files:
        category = target.split('/')[1] if '/' in target else 'other'
        files_by_category[category].append((original, os.path.basename(target)))

    for category in sorted(files_by_category.keys()):
        summary_content += f"\n### {category.replace('_', ' ').title()}\n"
        for original, filename in files_by_category[category]:
            summary_content += f"- `{filename}` (来自: {original})\n"

    summary_content += "\n## 📋 保留的当前测试文件\n\n"
    for original, target in kept_files:
        summary_content += f"- `{os.path.basename(target)}` - 当前使用中\n"

    summary_content += f"""
## 🔧 使用说明

### 存档文件位置
所有历史测试文件已移动到 `{archive_dir}/` 目录，按类型分类存放：
- `step_tests/` - Step相关测试
- `unified_tests/` - 统一审批测试
- `api_tests/` - API接口测试
- `wecom_tests/` - 企业微信相关测试
- `debug_tests/` - 调试和辅助文件
- `report_files/` - 测试报告文件
- `temp_files/` - 临时文件

### 当前测试文件
关键测试脚本保留在 `backend/tests_current/` 目录，可继续使用。

### 清理建议
1. **项目完成后**: 可以删除 `{archive_dir}/` 整个目录
2. **需要历史测试**: 从对应分类目录中找回
3. **保持整洁**: 定期清理临时文件和日志

## ⚠️ 注意事项

- 归档的文件仍然保留，未被删除
- 当前正在使用的测试脚本已复制到专门目录
- 可以随时从归档中恢复需要的文件
- 建议项目完成验收后再考虑彻底删除归档文件

---
**生成工具**: 测试文件清理脚本
**项目**: 芯片报价系统统一审批模块
"""

    # 保存总结报告
    with open(f"{archive_dir}/CLEANUP_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(summary_content)

    print(f"   📋 创建清理报告: {archive_dir}/CLEANUP_SUMMARY.md")

def show_directory_structure():
    """显示清理后的目录结构"""
    print("\n📁 清理后的目录结构:")

    # 显示存档目录
    if os.path.exists("testing_archive"):
        print("\n🗂️ 测试文件存档 (testing_archive/):")
        for root, dirs, files in os.walk("testing_archive"):
            level = root.replace("testing_archive", "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files[:3]:  # 只显示前3个文件
                print(f"{subindent}{file}")
            if len(files) > 3:
                print(f"{subindent}... (+{len(files)-3} more files)")

    # 显示当前测试目录
    if os.path.exists("backend/tests_current"):
        print("\n📋 当前测试文件 (backend/tests_current/):")
        for file in os.listdir("backend/tests_current"):
            print(f"  {file}")

if __name__ == "__main__":
    print("🧹 测试文件清理工具")
    print("="*60)

    moved, kept = cleanup_test_files()
    show_directory_structure()

    print("\n" + "="*60)
    print("✅ 测试文件清理完成！")
    print("💡 查看 testing_archive/CLEANUP_SUMMARY.md 了解详情")