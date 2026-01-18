## 关联 Issue
Closes #

## 变更类型
- [ ] ✨ 新功能 (Feature)
- [ ] 🐛 修复 (Bug Fix)
- [ ] 📝 文档 (Documentation)
- [ ] ♻️ 重构 (Refactor)
- [ ] 🏗️ 基础设施/配置 (Infra/Config)

## 检查清单 (Checklist)

### 代码质量 (必填)
- [ ] **pre-commit 检查**: 已运行 `pre-commit run --all-files` 且全部通过
- [ ] **无格式化差异**: 代码已使用 `ruff format` 格式化
- [ ] **类型检查通过**: `mypy src/` 无错误

### 功能验证
- [ ] **测试覆盖**: 已添加/更新单元测试，并通过 CI
- [ ] **设计一致性**: 代码实现是否符合 `docs/design` 中的设计？

### 变更影响
- [ ] **数据库变更**: 是否包含 SQL 迁移脚本？(如有，请确认 `scripts/init_db.sql` 已同步)
- [ ] **配置变更**: 是否修改了 `.env.example` 或 `settings.py`？
- [ ] **依赖变更**: 是否修改了 `pyproject.toml`？

## 部署注意事项
<!-- 部署时是否需要特殊操作？如执行 SQL、重启服务等 -->
