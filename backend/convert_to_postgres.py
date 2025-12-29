#!/usr/bin/env python3
import re
import sys

print("开始转换SQLite到PostgreSQL格式...")

try:
    with open('sqlite_backup.sql', 'r', encoding='utf-8') as f:
        content = f.read()
except:
    with open('sqlite_backup.sql', 'r', encoding='latin-1') as f:
        content = f.read()

# 删除SQLite特有的内容
content = re.sub(r'PRAGMA.*?;\n', '', content)
content = re.sub(r'BEGIN TRANSACTION;', '', content)
content = re.sub(r'COMMIT;', '', content)
content = re.sub(r'DELETE FROM sqlite_sequence.*?;\n', '', content)
content = re.sub(r'INSERT INTO "?sqlite_sequence"?.*?;\n', '', content)
content = re.sub(r'CREATE UNIQUE INDEX.*?;\n', '', content, flags=re.MULTILINE)

# 只保留INSERT语句（因为服务器上表已存在）
lines = content.split('\n')
filtered_lines = []
for line in lines:
    if line.strip().startswith('INSERT INTO') or line.strip() == '':
        # 修复布尔值
        line = re.sub(r"VALUES\((.*?),0,", r"VALUES(\1,false,", line)
        line = re.sub(r"VALUES\((.*?),1,", r"VALUES(\1,true,", line)
        line = re.sub(r",0,", ",false,", line)
        line = re.sub(r",1,", ",true,", line)
        line = re.sub(r",0\)", ",false)", line)
        line = re.sub(r",1\)", ",true)", line)
        filtered_lines.append(line)

content = '\n'.join(filtered_lines)

# 保存转换后的文件
with open('postgres_import.sql', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 转换完成！文件: postgres_import.sql")

# 统计INSERT语句数量
insert_count = content.count('INSERT INTO')
print(f"  共有 {insert_count} 条INSERT语句")
