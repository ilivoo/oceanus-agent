.PHONY: help install dev lint format test test-unit test-cov clean docker-build docker-up docker-down

# 默认目标
help:
	@echo "Oceanus Agent - 可用命令:"
	@echo ""
	@echo "  install          安装生产依赖"
	@echo "  dev              安装开发依赖并设置 pre-commit"
	@echo "  lint             运行代码检查 (ruff + mypy)"
	@echo "  format           格式化代码"
	@echo "  test             运行所有测试"
	@echo "  test-unit        仅运行单元测试"
	@echo "  test-cov         运行测试并生成覆盖率报告"
	@echo "  clean            清理缓存文件"
	@echo "  docker-build     构建 Docker 镜像"
	@echo "  docker-up        启动本地开发环境"
	@echo "  docker-down      停止本地开发环境"

# 安装
install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install
	@echo "开发环境已设置完成!"

# 代码质量
lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# 测试
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit -v

test-cov:
	pytest tests/ -v --cov=oceanus_agent --cov-report=term-missing --cov-report=html

# 清理
clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ .coverage coverage.xml htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Docker
docker-build:
	docker build -t oceanus-agent:latest -f deploy/docker/Dockerfile .

docker-up:
	cd deploy/docker && docker compose up -d

docker-down:
	cd deploy/docker && docker compose down
