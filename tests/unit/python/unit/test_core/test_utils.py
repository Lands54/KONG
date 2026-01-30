"""
工具函数的单元测试
"""

import pytest
from dynhalting.core.path_utils import get_project_root, get_docred_data_path


class TestPathUtils:
    """测试路径工具函数"""
    
    def test_get_project_root(self):
        """测试获取项目根目录"""
        root = get_project_root()
        assert root is not None
        assert isinstance(root, str)
        # 检查是否包含 requirements.txt 或 README.md
        import os
        assert os.path.exists(os.path.join(root, "requirements.txt")) or \
               os.path.exists(os.path.join(root, "README.md"))
    
    def test_get_docred_data_path(self):
        """测试获取 DocRED 数据路径"""
        path = get_docred_data_path()
        assert path is not None
        assert "DocRED" in path
        assert "data" in path
