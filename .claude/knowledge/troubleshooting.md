# 故障排除指南

## 1. 数据库连接问题

### MySQL 连接失败

**症状**:

```text
sqlalchemy.exc.OperationalError: (aiomysql.err.OperationalError)
(2003, "Can't connect to MySQL server on 'localhost'")
```

**可能原因**:

1. MySQL 服务未启动
2. 网络配置错误
3. 认证失败

**排查步骤**:

```bash
# 1. 检查 MySQL 服务状态
docker compose ps  # 如果使用 Docker
systemctl status mysql  # 如果本地安装

# 2. 测试连接
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p

# 3. 检查环境变量
echo $MYSQL_HOST $MYSQL_PORT $MYSQL_USER
```

**解决方案**:

- 确保 MySQL 服务运行: `docker compose up -d mysql`
- 检查 `.env` 配置是否正确
- 确认防火墙/安全组允许连接

### Milvus 连接失败

**症状**:

```text
pymilvus.exceptions.MilvusException: <MilvusException: (code=2, message=Fail connecting to server)>
```

**排查步骤**:

```bash
# 1. 检查 Milvus 服务
docker compose ps | grep milvus

# 2. 测试 gRPC 端口
nc -zv $MILVUS_HOST $MILVUS_PORT

# 3. 检查 Collection 是否存在
python -c "from pymilvus import connections, utility; connections.connect(); print(utility.list_collections())"
```

---

## 2. LLM 调用问题

### OpenAI API 限流

**症状**:

```text
openai.RateLimitError: Rate limit reached for gpt-4o-mini
```

**解决方案**:

1. 使用指数退避重试 (已内置于 tenacity)
2. 增加 `OPENAI_MAX_RETRIES` 配置
3. 考虑升级 API 配额

### Token 超限

**症状**:

```text
openai.BadRequestError: This model's maximum context length is 128000 tokens
```

**解决方案**:

1. 检查 prompt 长度
2. 减少检索的相似案例数量
3. 截断过长的错误日志

**代码修复**:

```python
# 在 prompts.py 中添加截断逻辑
def truncate_error_message(msg: str, max_length: int = 4000) -> str:
    if len(msg) <= max_length:
        return msg
    return msg[:max_length] + "\n... (truncated)"
```

---

## 3. 工作流执行问题

### 状态不一致

**症状**:

- 诊断结果为空但状态显示 completed
- 重复处理同一个异常

**排查步骤**:

```sql
-- 检查异常状态
SELECT id, status, updated_at FROM job_exception
WHERE status IN ('pending', 'in_progress')
ORDER BY updated_at DESC LIMIT 10;

-- 检查是否有孤儿记录
SELECT je.id FROM job_exception je
LEFT JOIN diagnosis_result dr ON je.id = dr.exception_id
WHERE je.status = 'completed' AND dr.id IS NULL;
```

**解决方案**:

- 实现幂等性检查
- 添加状态转换日志
- 使用数据库事务保证原子性

### 无限循环/重试

**症状**:

- 同一个诊断任务反复执行
- `retry_count` 超过限制但未停止

**排查步骤**:

```python
# 在 LangSmith 中查看 trace
# 检查状态转换是否正确
# 验证路由条件
```

**解决方案**:

- 检查 `should_continue_after_diagnose` 路由逻辑
- 确保 `retry_count` 正确递增
- 添加最大运行时间检查

---

## 4. 常见代码错误

### 异步上下文错误

**症状**:

```text
RuntimeError: await wasn't used with future
RuntimeWarning: coroutine 'xxx' was never awaited
```

**解决方案**:

```python
# 错误
result = async_function()

# 正确
result = await async_function()
```

### Pydantic 验证错误

**症状**:

```text
pydantic.ValidationError: 1 validation error for Model
field_name
  Field required [type=missing, input_value=...]
```

**解决方案**:

```python
# 检查必填字段是否提供
# 检查字段类型是否匹配
# 使用 Optional 或默认值
```

---

## 5. 性能问题

### 诊断延迟过高

**可能原因**:

1. LLM API 响应慢
2. Milvus 检索效率低
3. 数据库查询未优化

**优化建议**:

```python
# 1. 并行检索
cases, docs = await asyncio.gather(
    milvus.search_cases(vector),
    milvus.search_docs(vector),
)

# 2. 添加索引
# CREATE INDEX idx_status ON job_exception (status, created_at);

# 3. 缓存 Embedding
@lru_cache(maxsize=1000)
async def get_cached_embedding(text_hash: str) -> List[float]:
    ...
```

---

## 6. 部署问题

### Docker 构建失败

**症状**:

```text
ERROR: failed to solve: process "/bin/sh -c pip install..." did not complete successfully
```

**排查步骤**:

```bash
# 本地测试安装
pip install -e ".[dev]"

# 检查 pyproject.toml 依赖
pip check
```

### K8s Pod CrashLoopBackOff

**排查步骤**:

```bash
kubectl logs -f deployment/oceanus-agent
kubectl describe pod <pod-name>
kubectl get events --sort-by='.lastTimestamp'
```
