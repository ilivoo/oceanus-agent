# /diagnose 命令

诊断代码问题或系统故障。

## 使用方式

```text
/diagnose [错误信息或问题描述]
```

## 执行流程

1. **收集信息**:
   - 解析错误信息
   - 查看相关代码文件
   - 检查最近的变更 (git log)

2. **分析根因**:
   - 定位错误源头
   - 检查相关依赖
   - 查阅故障排除知识库

3. **生成诊断报告**:
   - 根因分析
   - 修复建议
   - 预防措施

## 常见问题类别

### 数据库连接

- MySQL 连接超时
- Milvus 集合不存在
- 事务死锁

### LLM 调用

- OpenAI API 限流
- Token 超限
- 响应解析失败

### 工作流执行

- 状态不一致
- 节点重试失败
- 无限循环

## 关联知识库

| 知识库 | 用途 |
|--------|------|
| [troubleshooting.md](../knowledge/troubleshooting.md) | 常见问题和解决方案 |
| [architecture.md](../knowledge/architecture.md) | 系统依赖关系排查 |
| [patterns.md](../knowledge/patterns.md) | 正确的代码模式参考 |

## 相关文档

- [命令总览](README.md)
- [开发指南 - 常见问题](../../docs/guides/development.md)
- [端到端示例](../../docs/guides/workflow-example.md)
