# 部署指南

## 1. Docker 部署

### 1.1 构建镜像

```bash
cd /path/to/oceanus-agent
docker build -t oceanus-agent:latest -f deploy/docker/Dockerfile .
```

### 1.2 本地测试

```bash
cd deploy/docker

# 设置环境变量
export OPENAI_API_KEY=sk-xxx
export LANGCHAIN_API_KEY=ls-xxx

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f agent
```

### 1.3 仅启动依赖

```bash
# 仅启动 MySQL 和 Milvus
docker-compose up -d mysql milvus etcd minio

# 本地运行 Agent
python -m oceanus_agent
```

## 2. Kubernetes 部署

### 2.1 前置条件

- 已有 K8s 集群
- 已部署 MySQL（或使用云数据库）
- 已部署 Milvus（或使用 Zilliz Cloud）
- kubectl 已配置

### 2.2 创建命名空间

```bash
kubectl apply -f deploy/k8s/namespace.yaml
```

### 2.3 配置 Secret

编辑 `deploy/k8s/secret.yaml`，填入真实密钥：

```yaml
stringData:
  MYSQL_USER: "oceanus"
  MYSQL_PASSWORD: "your-real-password"
  OPENAI_API_KEY: "sk-your-real-api-key"
  LANGCHAIN_API_KEY: "ls-your-real-api-key"
```

```bash
kubectl apply -f deploy/k8s/secret.yaml
```

### 2.4 配置 ConfigMap

编辑 `deploy/k8s/configmap.yaml`，更新连接地址：

```yaml
data:
  MYSQL_HOST: "mysql.database.svc.cluster.local"
  MILVUS_HOST: "milvus.vector-db.svc.cluster.local"
```

```bash
kubectl apply -f deploy/k8s/configmap.yaml
```

### 2.5 部署应用

```bash
# 更新镜像地址
# 编辑 deploy/k8s/deployment.yaml
# image: your-registry/oceanus-agent:latest

kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
kubectl apply -f deploy/k8s/hpa.yaml
```

### 2.6 验证部署

```bash
# 查看 Pod 状态
kubectl get pods -n oceanus-agent

# 查看日志
kubectl logs -f deployment/oceanus-agent -n oceanus-agent

# 查看 HPA 状态
kubectl get hpa -n oceanus-agent
```

## 3. 配置说明

### 3.1 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| APP_ENV | 环境 | development |
| LOG_LEVEL | 日志级别 | INFO |
| MYSQL_HOST | MySQL 地址 | localhost |
| MYSQL_PORT | MySQL 端口 | 3306 |
| MILVUS_HOST | Milvus 地址 | localhost |
| MILVUS_PORT | Milvus 端口 | 19530 |
| OPENAI_API_KEY | OpenAI API Key | - |
| OPENAI_MODEL | 使用的模型 | gpt-4o-mini |
| SCHEDULER_INTERVAL_SECONDS | 扫描间隔 | 60 |
| SCHEDULER_BATCH_SIZE | 批量大小 | 10 |
| KNOWLEDGE_CONFIDENCE_THRESHOLD | 知识积累阈值 | 0.8 |

### 3.2 资源配置

**推荐配置:**

| 规模 | CPU | 内存 | 副本数 |
|------|-----|------|--------|
| 小 (<100/天) | 250m | 512Mi | 1 |
| 中 (100-1000/天) | 500m | 1Gi | 2 |
| 大 (>1000/天) | 1000m | 2Gi | 3-5 |

## 4. 监控

### 4.1 日志查看

```bash
# K8s
kubectl logs -f deployment/oceanus-agent -n oceanus-agent

# Docker
docker-compose logs -f agent
```

### 4.2 指标监控

Agent 暴露 Prometheus 指标（如已配置）：

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/metrics"
```

### 4.3 LangSmith 监控

访问 https://smith.langchain.com 查看：
- 工作流执行追踪
- LLM 调用详情
- 错误分析

## 5. 故障排查

### 5.1 Pod 无法启动

```bash
# 查看事件
kubectl describe pod <pod-name> -n oceanus-agent

# 常见原因:
# - 镜像拉取失败
# - 配置缺失
# - 依赖服务不可用
```

### 5.2 连接数据库失败

```bash
# 测试连接
kubectl run mysql-test --rm -it --image=mysql:8.0 -- \
  mysql -h mysql.database.svc.cluster.local -u oceanus -p

# 检查 Service 是否正确
kubectl get svc -n database
```

### 5.3 LLM 调用失败

```bash
# 检查 API Key
kubectl get secret oceanus-agent-secrets -n oceanus-agent -o yaml

# 测试网络
kubectl exec -it <pod-name> -n oceanus-agent -- \
  curl https://api.openai.com/v1/models
```

## 6. 升级

### 6.1 滚动升级

```bash
# 更新镜像
kubectl set image deployment/oceanus-agent \
  agent=your-registry/oceanus-agent:v2.0.0 \
  -n oceanus-agent

# 查看升级状态
kubectl rollout status deployment/oceanus-agent -n oceanus-agent
```

### 6.2 回滚

```bash
# 查看历史
kubectl rollout history deployment/oceanus-agent -n oceanus-agent

# 回滚到上一版本
kubectl rollout undo deployment/oceanus-agent -n oceanus-agent
```

## 7. 备份与恢复

### 7.1 数据库备份

```bash
# MySQL 备份
mysqldump -h <host> -u oceanus -p oceanus_agent > backup.sql

# 恢复
mysql -h <host> -u oceanus -p oceanus_agent < backup.sql
```

### 7.2 Milvus 备份

参考 Milvus 官方文档进行集合备份。
