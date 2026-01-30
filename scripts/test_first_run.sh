#!/bin/bash

echo "=== 测试系统状态 ==="

# 测试 Python 服务
echo -n "Python 服务: "
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 未运行"
fi

# 测试 Node.js 服务
echo -n "Node.js 服务: "
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 未运行"
fi

echo ""
echo "如果服务都在运行，可以创建测试实验："
echo 'curl -X POST http://localhost:3000/api/experiments \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"name": "测试实验", "goal": "测试", "text": "测试文本", "haltingStrategy": "RULE_BASED"}'"'"
