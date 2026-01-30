#!/bin/bash

# 检查 OpenRouter API Key 是否设置

echo "=== 检查 OpenRouter API Key ==="
echo ""

# 检查环境变量
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ 环境变量 OPENROUTER_API_KEY 未设置"
    echo ""
    echo "设置方法："
    echo "  export OPENROUTER_API_KEY='your-api-key-here'"
    echo ""
    echo "永久设置（添加到 ~/.zshrc）："
    echo "  echo 'export OPENROUTER_API_KEY=\"your-api-key-here\"' >> ~/.zshrc"
    echo "  source ~/.zshrc"
    echo ""
    echo "获取 API Key: https://openrouter.ai/keys"
    exit 1
else
    echo "✅ 环境变量 OPENROUTER_API_KEY 已设置"
    echo "   长度: ${#OPENROUTER_API_KEY} 字符"
    echo "   预览: ${OPENROUTER_API_KEY:0:15}..."
    echo ""
fi

# 检查 Python 服务（如果运行）
if curl -s http://localhost:8000/api/v1/config/check > /dev/null 2>&1; then
    echo "✅ Python 服务运行中"
    echo ""
    echo "配置状态："
    curl -s http://localhost:8000/api/v1/config/check | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/v1/config/check
    echo ""
else
    echo "⚠️  Python 服务未运行（http://localhost:8000）"
    echo "   请先启动 Python 服务："
    echo "   cd backend/python_service"
    echo "   export OPENROUTER_API_KEY='your-api-key-here'"
    echo "   python main.py"
    echo ""
fi

echo "=== 检查完成 ==="
