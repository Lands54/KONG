"""
判停模块的单元测试
"""

import pytest
from dynhalting.halting.module import HaltingModule
from dynhalting.core.graph import Graph, Node, NodeType
from tests.python.fixtures.sample_graphs import create_simple_graph


class TestHaltingModule:
    """测试判停模块"""
    
    @pytest.fixture
    def halting_module(self):
        """创建判停模块实例"""
        return HaltingModule(mode="RULE_BASED")
    
    def test_halting_module_initialization(self, halting_module):
        """测试判停模块初始化"""
        assert halting_module is not None
        from dynhalting.halting.module import HaltingMode
        assert halting_module.mode == HaltingMode.RULE_BASED
    
    def test_evaluate_graph_always_loop(self):
        """测试 ALWAYS_LOOP 模式的节点评估"""
        module = HaltingModule(mode="ALWAYS_LOOP")
        graph = create_simple_graph()
        evaluated_graph = module.evaluate_graph(graph, "test goal", depth=0, iteration=1)
        
        # 所有节点应该被标记为 LOOP
        for node in evaluated_graph.nodes.values():
            assert node.metadata.get('status') == 'LOOP'
        
        # 全局决策应该是 CONTINUE
        global_decision = module.should_halt_global(evaluated_graph, "test goal", depth=0, iteration=1)
        assert global_decision == "CONTINUE"
    
    def test_evaluate_graph_always_halt(self):
        """测试 ALWAYS_HALT 模式的节点评估"""
        module = HaltingModule(mode="ALWAYS_HALT")
        graph = create_simple_graph()
        evaluated_graph = module.evaluate_graph(graph, "test goal", depth=0, iteration=1)
        
        # 所有节点应该被标记为 HALT-ACCEPT
        for node in evaluated_graph.nodes.values():
            assert node.metadata.get('status') == 'HALT-ACCEPT'
        
        # 全局决策应该是 HALT
        global_decision = module.should_halt_global(evaluated_graph, "test goal", depth=0, iteration=1)
        assert global_decision == "HALT"
    
    def test_evaluate_graph_rule_based(self, halting_module):
        """测试 RULE_BASED 模式的节点评估"""
        graph = create_simple_graph()
        evaluated_graph = halting_module.evaluate_graph(graph, "test goal", depth=0, iteration=1)
        
        # 每个节点应该有状态
        for node in evaluated_graph.nodes.values():
            status = node.metadata.get('status')
            assert status in ['HALT-ACCEPT', 'HALT-DROP', 'LOOP', 'HITL']
        
        # 全局决策应该是有效的
        global_decision = halting_module.should_halt_global(evaluated_graph, "test goal", depth=0, iteration=1)
        assert global_decision in ["HALT", "CONTINUE", "DROP", "HITL"]
