import pytest
import sys
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.parent.parent.absolute()

# 核心路径注入
sys.path.insert(0, str(project_root / "server" / "python"))
sys.path.insert(0, str(project_root / "core"))
sys.path.insert(0, str(project_root / "server" / "python" / "python_service"))

# 注入虚假环境变量以通过初始化检查
os.environ["OPENROUTER_API_KEY"] = "sk-test-key-for-unit-tests"
os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)

@pytest.fixture
def sample_text():
    return "Google was founded by Larry Page and Sergey Brin in September 1998."

@pytest.fixture
def sample_goal():
    return "Extract founders of Google"
