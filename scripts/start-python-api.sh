#!/bin/bash
# 启动 Python API 服务

# 设置项目根目录
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 将 core 和 server/python 添加到 PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}/core:${PROJECT_ROOT}/server/python:${PYTHONPATH}"

# 切换到 server/python 目录
cd "${PROJECT_ROOT}/server/python"

# 启动服务
python3 python_service/main.py
