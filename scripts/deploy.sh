#!/bin/bash
# WenNian deployment script
set -e

echo "=== 问年 WenNian v2.0 部署脚本 ==="
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "需要安装Docker"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "需要安装docker-compose"; exit 1; }

# Build and deploy
echo "[1/3] 构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build

echo "[2/3] 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

echo "[3/3] 运行健康检查..."
sleep 5
if curl -s http://localhost:8000/api/v1/health | grep -q "ok"; then
    echo "✓ API服务健康检查通过"
else
    echo "✗ API服务健康检查失败"
    exit 1
fi

echo ""
echo "=== 部署完成 ==="
echo "API: http://localhost:8000"
echo "Gradio UI: http://localhost:7860"
echo ""
echo "查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.prod.yml down"
