# 服务状态报告

## 生成时间
2026-01-25 19:22

## 服务状态

### ✅ Python API 服务
- **状态**: 运行中
- **端口**: 8000
- **启动命令**: `./scripts/start-python-api.sh`
- **健康检查**: http://localhost:8000/
- **API 文档**: http://localhost:8000/docs

**组件状态**:
- ✅ 组件发现: 13 个组件
- ✅ REBEL 模型: 已加载
- ✅ Embedding 模型: 已加载

### ✅ Node API 服务
- **状态**: 运行中
- **端口**: 3000
- **启动命令**: `./scripts/start-node-api.sh`
- **数据库**: SQLite (`server/node/prisma/dev.db`)

**修复内容**:
- ✅ 添加 `DATABASE_URL` 到 `.env`
- ✅ 初始化 Prisma 数据库
- ✅ 更新启动脚本加载环境变量

### ✅ Web 前端
- **状态**: 运行中
- **端口**: 5173 (Vite 默认)
- **启动命令**: `./scripts/start-web.sh`
- **访问地址**: http://localhost:5173

## 环境配置

### .env 文件
```bash
OPENROUTER_API_KEY=sk-or-v1-***
DATABASE_URL="file:./server/node/prisma/dev.db"
```

### PYTHONPATH
```bash
export PYTHONPATH="${PROJECT_ROOT}/core:${PROJECT_ROOT}/server/python:${PYTHONPATH}"
```

## 端口分配

| 服务 | 端口 | 协议 |
|------|------|------|
| Python API | 8000 | HTTP |
| Node API | 3000 | HTTP + WebSocket |
| Web 前端 | 5173 | HTTP |

## 快速命令

### 启动所有服务
```bash
# 终端 1
./scripts/start-python-api.sh

# 终端 2
./scripts/start-node-api.sh

# 终端 3
./scripts/start-web.sh
```

### 停止所有服务
```bash
pkill -f "python.*main.py"
pkill -f "tsx.*server.ts"
pkill -f "vite"
```

### 查看日志
```bash
# Python API 日志在启动终端
# Node API 日志在启动终端
# Web 前端日志在启动终端
```

## 数据库管理

### 查看数据库
```bash
cd server/node
npx prisma studio
```

### 重置数据库
```bash
cd server/node
npx prisma db push --force-reset
```

### 生成 Prisma Client
```bash
cd server/node
npx prisma generate
```

## 测试端点

### Python API
```bash
# 健康检查
curl http://localhost:8000/

# 组件列表
curl http://localhost:8000/api/v1/config/components

# API 文档
open http://localhost:8000/docs
```

### Node API
```bash
# 实验列表
curl http://localhost:3000/api/experiments

# WebSocket 连接
# ws://localhost:3000
```

### Web 前端
```bash
# 打开浏览器
open http://localhost:5173
```

## 已知问题

### 1. FastAPI Deprecation Warning
```
on_event is deprecated, use lifespan event handlers instead.
```
**影响**: 无，仅警告  
**计划**: 未来迁移到 lifespan 事件处理器

### 2. 端口冲突
如果端口被占用，可以修改配置：
- Python API: `server/python/python_service/main.py` (line 93)
- Node API: `server/node/src/server.ts`
- Web: `web/vite.config.ts`

## 下一步

1. ✅ 所有服务已启动
2. ⏭️ 在浏览器中测试完整流程
3. ⏭️ 运行集成测试
4. ⏭️ 检查前后端连接
