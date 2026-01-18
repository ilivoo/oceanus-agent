# /design 命令

生成功能设计文档。

## 使用方式

```text
/design [功能描述]
```

## 执行流程

1. **分析需求**: 解析用户提供的功能描述
2. **检索上下文**:
   - 阅读相关的现有设计文档 (docs/design/)
   - 查看相关代码模块
   - 检查是否有类似功能实现
3. **生成设计文档**: 使用 docs/templates/design-template.md 模板
4. **输出位置建议**: docs/design/[feature-name].md

## 设计文档要求

- 必须包含架构图 (ASCII 或 Mermaid)
- 必须定义 Pydantic 数据模型
- 必须包含测试策略
- 必须评估对现有系统的影响

## 关联知识

- 项目架构: .claude/knowledge/architecture.md
- 代码模式: .claude/knowledge/patterns.md
- 设计模板: docs/templates/design-template.md
