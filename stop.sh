#!/bin/bash

# KONG System Shutdown Script
# ---------------------------------------
# 此脚本用于安全地关闭 KONG 的所有后端服务进程。

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}正在尝试关闭 KONG 全量服务进程...${NC}"

# 1. 关闭 Python 服务 (通常监听 8000 端口)
echo -e "${YELLOW}检查 Python 推理服务 (Port 8000)...${NC}"
PYTHON_PIDS=$(lsof -t -i:8000)
if [ -z "$PYTHON_PIDS" ]; then
    echo -e "Python 服务未运行。"
else
    echo -e "${RED}发现进程: $PYTHON_PIDS，正在终止...${NC}"
    kill $PYTHON_PIDS
    sleep 1
    echo -e "${GREEN}✓ Python 服务已关闭。${NC}"
fi

# 2. 关闭 Node.js 服务 (通常监听 3000 端口)
echo -e "${YELLOW}检查 Node.js 中间件服务 (Port 3000)...${NC}"
NODE_PIDS=$(lsof -t -i:3000)
if [ -z "$NODE_PIDS" ]; then
    echo -e "Node.js 服务未运行。"
else
    echo -e "${RED}发现进程: $NODE_PIDS，正在终止...${NC}"
    kill $NODE_PIDS
    sleep 1
    echo -e "${GREEN}✓ Node.js 服务已关闭。${NC}"
fi

# 3. 强制清理残留 (按名称搜索)
echo -e "${YELLOW}清理残留进程隔离区...${NC}"
# 清理可能存在的 uvicorn 进程
pkill -f "uvicorn python_service.main:app" > /dev/null 2>&1
# 清理可能存在的 node 进程 (如果有特定名称)
pkill -f "node src/server.ts" > /dev/null 2>&1

echo -e "\n${GREEN}=======================================${NC}"
echo -e "${GREEN}  KONG 环境清理完成，所有端口已释放。  ${NC}"
echo -e "${GREEN}=======================================${NC}"
