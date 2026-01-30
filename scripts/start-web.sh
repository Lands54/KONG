#!/bin/bash
# 启动 Web 前端

# 设置项目根目录
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 切换到 web 目录
cd "${PROJECT_ROOT}/web"

# 启动服务
npm run dev
