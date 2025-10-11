# Git 分支管理指南

## 当前分支结构

### 本地分支
```
* quote-detail-editable-claude  -> cccf8b5 (当前工作分支)
  feature/next-task            -> 12d1f80 (其他功能分支)
  main                         -> 12d1f80 (主分支)
```

### 远程仓库分支

#### Gitee (origin) - 主仓库
```
quote-detail-editable-claude  -> cccf8b5 (当前工作)
feature/next-task            -> 12d1f80 (保持独立)
main                         -> 12d1f80 (稳定版本)
```

#### GitHub (github) - 镜像仓库
```
quote-detail-editable-claude  -> cccf8b5 (镜像同步)
feature/next-task            -> 12d1f80 (保持独立)
main                         -> 12d1f80 (稳定版本)
```

## 分支说明

### quote-detail-editable-claude
- **用途**: 当前的功能开发分支（报价单详情可编辑等功能）
- **跟踪**: origin/quote-detail-editable-claude
- **提交数**: 比 main 超前 47 个提交
- **状态**: 活跃开发中

### feature/next-task
- **用途**: 独立的功能分支（可能用于其他任务）
- **跟踪**: github/feature/next-task
- **状态**: 与 main 同步
- **注意**: ⚠️ 此分支应保持独立，不要与当前工作分支混淆

### main
- **用途**: 主分支，稳定版本
- **跟踪**: origin/main
- **状态**: 稳定

## 日常工作流程

### 1. 提交代码
```bash
git add .
git commit -m "feat: 你的提交信息"
```

### 2. 推送到两个远程仓库（推荐）
```bash
./push_all.sh
```

这个脚本会：
- ✅ 自动检测当前分支
- ✅ 推送到 Gitee 的同名分支
- ✅ 推送到 GitHub 的同名分支
- ✅ 不会影响其他分支

### 3. 手动推送（备选）
```bash
# 只在当前分支上推送
git push origin quote-detail-editable-claude
git push github quote-detail-editable-claude
```

## ⚠️ 重要注意事项

### 不要做的事情

❌ **不要跨分支推送**
```bash
# 错误示例 - 会破坏 feature/next-task 分支
git push github HEAD:feature/next-task
```

❌ **不要强制推送到不属于你的分支**
```bash
# 除非你明确知道后果
git push -f origin feature/next-task
```

❌ **不要混淆分支名称**
- 在 `quote-detail-editable-claude` 上工作时，只推送到同名分支
- 不要推送到 `feature/next-task`

### 应该做的事情

✅ **始终使用 push_all.sh 脚本**
- 确保推送到正确的分支
- 避免人为错误

✅ **推送前检查当前分支**
```bash
git branch  # 查看当前分支
git status  # 查看状态
```

✅ **定期同步（如果需要）**
```bash
git fetch origin
git fetch github
```

## 分支跟踪配置

当前配置（已优化）：
```
quote-detail-editable-claude -> origin/quote-detail-editable-claude
feature/next-task            -> github/feature/next-task
main                         -> origin/main
```

如果需要修改跟踪分支：
```bash
git branch --set-upstream-to=origin/分支名 本地分支名
```

## 快速命令参考

```bash
# 查看所有分支状态
git branch -vv

# 查看远程分支
git ls-remote --heads origin
git ls-remote --heads github

# 切换分支
git checkout 分支名

# 推送当前分支到两个仓库
./push_all.sh

# 查看提交历史
git log --oneline -10

# 查看分支差异
git log main..quote-detail-editable-claude
```

## 问题排查

### 如果推送到错误的分支

1. **立即停止**
2. **恢复原分支**
   ```bash
   # 恢复到原来的提交
   git push origin 正确的commit哈希:分支名 -f
   git push github 正确的commit哈希:分支名 -f
   ```

### 如果不确定当前状态

```bash
# 检查所有远程分支
git ls-remote --heads origin
git ls-remote --heads github

# 检查本地分支
git branch -vv

# 检查提交历史
git log --graph --oneline --all -10
```

## 总结

- ✅ 使用 `./push_all.sh` 脚本推送（最安全）
- ✅ 只在当前分支上工作
- ✅ 推送到同名分支
- ❌ 不要跨分支推送
- ❌ 不要混淆 `quote-detail-editable-claude` 和 `feature/next-task`
