import os
from typing import Any, Dict, Optional
from kgforge.components.base import BaseExpander
from kgforge.components.expanders.utils.gpt_expander import GPTExpander
from kgforge.models import Graph

class GPTExpanderAppliance(BaseExpander):
    """
    基于 GPT 的目标分解/节点拓展器具
    """
    name = "gpt"
    display_name = "GPT 展开器"

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 合并参数
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        super().__init__(mapped_config)
        
        default_model = os.getenv("DEFAULT_MODEL", "openai/gpt-4-turbo-preview")
        
        self.expander = GPTExpander(
            model=self.config.get("model", default_model),
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),
            temperature=self.config.get("temperature", 0.7)
        )

    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        """获取组件规范"""
        default_model = os.getenv("DEFAULT_MODEL", "openai/gpt-4-turbo-preview")
        return {
            "id": "gpt",
            "name": "GPT 展开器",
            "description": "基于 GPT 模型的 Top-Down 目标驱动图扩展。",
            "params": {
                "model": {
                    "type": "string",
                    "default": default_model,
                    "description": "GPT 模型名称"
                },
                "max_nodes": {
                    "type": "integer",
                    "default": 10,
                    "description": "最大扩展节点数"
                },
                "temperature": {
                    "type": "number",
                    "default": 0.7,
                    "description": "采样温度"
                },
                "base_url": {
                    "type": "string",
                    "default": "https://openrouter.ai/api/v1",
                    "description": "API 基准地址"
                }
            }
        }

    def expand_goal(self, goal: str, **kwargs) -> Graph:
        """实现 IExpander 接口"""
        return self.expander.expand_goal(goal, **kwargs)

    def expand_graph(self, graph: Graph, **kwargs) -> Graph:
        """实现 IExpander 接口"""
        return self.expander.expand_graph(graph, **kwargs)
