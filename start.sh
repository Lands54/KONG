#!/bin/bash

# KONG All-in-One Launcher
# 同时启动 Python 推理服务、Node.js 适配层和前端 UI

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}    KONG Research Framework - All-in-One      ${NC}"
echo -e "${BLUE}==============================================${NC}"

# 获取脚本所在目录作为根目录
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 加载全局环境变量
if [ -f "$ROOT_DIR/.env" ]; then
    echo -e "${BLUE}正在加载 .env 配置文件...${NC}"
    # 修复导出逻辑，确保值中的空格或特殊字符被正确处理
    set -a
    source "$ROOT_DIR/.env"
    set +a
fi

# 退出处理：清理所有后台进程
cleanup() {
    echo -e "\n${PURPLE}正在停止所有服务...${NC}"
    pkill -P $$
    exit
}

trap cleanup SIGINT SIGTERM

# 1. 启动 Python 推理服务
echo -e "${GREEN}[1/3] 正在启动 Python 推理服务 (Port 8000)...${NC}"
(
    cd "$ROOT_DIR/server/python/python_service"
    export PYTHONPATH="$ROOT_DIR/server/python:$ROOT_DIR/core:$PYTHONPATH"
    python main.py
) &

# 2. 启动 Node.js 适配层
# 关键修复：在 server/node 目录下启动，环境变量使用相对路径时必须考虑工作目录
echo -e "${GREEN}[2/3] 正在启动 Node.js 中继服务 (Port 3001)...${NC}"
(
    cd "$ROOT_DIR/server/node"
    # 这里环境变量已经在上方 export，Node 进程会继承它
    npm run dev
) &

# 3. 启动前端 UI
echo -e "${GREEN}[3/3] 正在启动前端 Web UI (Port 5173)...${NC}"
(
    cd "$ROOT_DIR/web"
    npm run dev
) &

echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}✓ 所有服务已在后台启动！${NC}"
echo -e "Python API: http://localhost:8000"
echo -e "Node Relay: http://localhost:3001"
echo -e "Web UI:     http://localhost:5173"
echo -e "${BLUE}按 [Ctrl+C] 停止所有服务${NC}"
echo -e "${BLUE}==============================================${NC}"

# 保持脚本运行，等待信号
wait
