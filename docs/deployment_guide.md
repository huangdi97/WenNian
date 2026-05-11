# 问年 WenNian 部署指南 v2.0.0

## 系统要求
- Docker 20.10+
- docker-compose 2.0+
- 4GB RAM, 2 CPU cores

## 快速部署
```bash
# 克隆项目
cd wennian

# 一键部署
bash scripts/deploy.sh
```

## 手动部署
```bash
# 1. 构建镜像
docker-compose -f docker-compose.prod.yml build

# 2. 启动
docker-compose -f docker-compose.prod.yml up -d

# 3. 验证
curl http://localhost:8000/api/v1/health
```

## 环境变量
| 变量 | 说明 | 默认值 |
|------|------|--------|
| WENNIAN_API__HOST | API绑定地址 | 0.0.0.0 |
| WENNIAN_API__PORT | API端口 | 8000 |
| WENNIAN_LOGGING__LEVEL | 日志级别 | INFO |

## 服务端口
- API: 8000
- Gradio UI: 7860
- Nginx: 80/443

## 停止服务
```bash
docker-compose -f docker-compose.prod.yml down
```

## 数据持久化
- 日志: `./logs`
- 数据: `./data`
- 配置: `./config`
