"""
闭环编排的单元测试
"""

import pytest
from dynhalting.orchestration.loop import DynamicHaltingLoop
from dynhalting.core.graph import Graph


@pytest.mark.unit
class TestDynamicHaltingLoop:
    """测试动态判停闭环"""
    
    @pytest.fixture
    def loop(self):
        """创建闭环实例"""
        import os
        # 从环境变量获取 API Key，如果没有则跳过测试
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("需要设置 OPENROUTER_API_KEY 环境变量才能运行此测试")
        return DynamicHaltingLoop(
            max_depth=2,
            max_nodes=10,
            max_iterations=3,
            gpt_api_key=api_key
        )
    
    def test_loop_initialization(self, loop):
        """测试闭环初始化"""
        assert loop is not None
        assert loop.max_depth == 2
        assert loop.max_nodes == 10
        assert loop.max_iterations == 3
    
    @pytest.mark.skip(reason="需要模型和 API，跳过完整测试")
    def test_run_loop(self, loop, sample_goal, sample_text):
        """测试运行闭环"""
        # 注意：这需要模型加载和 API 调用
        result = loop.run(sample_goal, sample_text, verbose=False)
        assert result is not None
        assert isinstance(result.graph, Graph)
