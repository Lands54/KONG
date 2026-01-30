#!/bin/bash
# 启动 Node.js API 服务

# 设置项目根目录
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 加载环境变量
if [ -f "${PROJECT_ROOT}/.env" ]; then
    export $(cat "${PROJECT_ROOT}/.env" | grep -v '^#' | xargs)
fi

# 切换到 server/node 目录
cd "${PROJECT_ROOT}/server/node"

# 修正 DATABASE_URL 路径 (因为我们已经 cd 到了子目录)
export DATABASE_URL="file:./prisma/dev.db"

# 启动服务
npm run dev
