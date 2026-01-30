"""
GPT 目标分解器 (Core Implementation)
使用 OpenRouter API 实现 Top-Down 任务分解逻辑
将需求目标递归拆解为子系统节点,构建目标初解图 G_T
纯粹的业务逻辑类，不依赖系统协议
"""

from typing import List, Dict, Any, Optional
import json
import os
from openai import OpenAI
from kgforge.models import Graph, Node, Edge
from kgforge.utils import get_logger

logger = get_logger(__name__)

# 局部默认配置 (Local implementation defaults)
DEFAULT_GPT_MODEL = "openai/gpt-4"
DEFAULT_GPT_MAX_NODES = 10
DEFAULT_GPT_MAX_SUBNODES = 5
DEFAULT_GPT_TEMPERATURE = 0.7
DEFAULT_API_BASE_URL = "https://openrouter.ai/api/v1"

class GPTExpander:
    """GPT 目标分解器核心逻辑"""
    
    def __init__(
        self,
        model: str = DEFAULT_GPT_MODEL,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = DEFAULT_GPT_TEMPERATURE,
        **kwargs
    ):
        self.model = model
        self.temperature = temperature
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API Key 未设置。请设置环境变量 OPENROUTER_API_KEY 或传入 api_key 参数\n"
                "获取 API Key: https://openrouter.ai/keys"
            )
        
        if base_url is None:
            base_url = DEFAULT_API_BASE_URL
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def expand_goal(self, goal: str, max_nodes: Optional[int] = None) -> Graph:
        """[Text -> Graph] 将文本目标转化为初始图 (G_T)"""
        max_nodes = max_nodes or DEFAULT_GPT_MAX_NODES
        prompt = self._build_goal_prompt(goal, max_nodes)
        return self._call_llm_and_build_graph(prompt, goal)

    def expand_graph(self, graph: Graph, **kwargs) -> Graph:
        """[Graph -> Graph] 基于全图上下文，智能选择节点并展开"""
        # 序列化当前图上下文
        context = self._serialize_graph_context(graph)
        
        # 构建图扩展提示词
        prompt = self._build_graph_expansion_prompt(context, DEFAULT_GPT_MAX_SUBNODES)
        
        # 调用 LLM 并构建增量图
        return self._call_llm_and_build_graph(prompt, "graph_expansion")

    def _serialize_graph_context(self, graph: Graph) -> str:
        """将图序列化为 LLM 可读的 JSON 上下文"""
        nodes_info = []
        for n in graph.nodes.values():
            nodes_info.append({
                "id": n.id,
                "label": n.attr("label"),
                "type": n.attr("node_type", "mixed"),
                "description": n.meta("description", ""),
                "ablation_value": n.metric("ablation_value", 0.0),
                "expanded": n.state("expanded", False),
                "expandable": n.state("expandable", True)
            })
        
        edges_info = []
        for e in graph.edges:
            edges_info.append({
                "source": e.source,
                "target": e.target,
                "relation": e.attr("relation")
            })
            
        return json.dumps({
            "goal": graph.metadata.get("goal", ""),
            "nodes": nodes_info,
            "edges": edges_info
        }, ensure_ascii=False, indent=2)

    def _build_goal_prompt(self, goal: str, max_nodes: int) -> str:
        """构建初始目标分解提示词"""
        return f"""请将以下需求目标分解为结构化的系统层级图。

需求目标：{goal}

要求：
1. 将目标分解为多个子系统/模块节点
2. 定义节点之间的关系（如：依赖、包含、交互等）
3. 节点数量控制在 {max_nodes} 个以内
4. 每个节点应该有清晰的标签和功能描述

请以 JSON 格式输出，格式如下：
{{
  "nodes": [
    {{
      "id": "node_1",
      "label": "节点名称",
      "description": "节点功能描述",
      "type": "system" 或 "concept" 或 "entity"
    }}
  ],
  "edges": [
    {{
      "source": "node_1",
      "target": "node_2",
      "relation": "关系类型（如：depends_on, contains, interacts_with）"
    }}
  ]
}}

请直接输出 JSON，不要包含其他文字说明。"""

    def _build_graph_expansion_prompt(self, graph_context: str, max_nodes: int) -> str:
        """构建图扩展提示词"""
        return f"""当前系统架构图状态如下（JSON 格式）：

{graph_context}

你的任务：
1. 分析上述图结构，关注每个节点的 ablation_value（评分）和 expanded（是否已展开）状态
2. 选择**一个**最需要展开的节点（通常是：评分高、未展开、可展开的节点）
3. 为该节点生成详细的子结构（子图），节点数量控制在 {max_nodes} 个左右
4. 确保新生成的子节点通过边连接到你选择的父节点

请输出 JSON 格式，包含本轮生成的增量内容：
{{
  "parent_node_id": "你选择展开的父节点ID",
  "reason": "选择该节点的理由",
  "nodes": [
    {{
      "id": "new_node_1",
      "label": "子节点名称",
      "description": "子节点描述",
      "type": "system"
    }}
  ],
  "edges": [
    {{
      "source": "parent_node_id",
      "target": "new_node_1",
      "relation": "contains"
    }},
    {{
      "source": "new_node_1",
      "target": "new_node_2",
      "relation": "depends_on"
    }}
  ]
}}

注意：edges 中必须包含父节点到新子节点的连接边。
请直接输出 JSON，不要包含其他文字说明。"""

    def _call_llm_and_build_graph(self, prompt: str, context_label: str) -> Graph:
        """调用 LLM 并构建图"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个系统架构师，擅长将复杂需求分解为结构化的系统层级图。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            error_msg = (
                f"OpenRouter API 调用失败: {e}\n"
                f"请检查 OPENROUTER_API_KEY 环境变量和网络连接"
            )
            # logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        
        if not response.choices or not response.choices[0].message.content:
            raise RuntimeError("GPT API 返回空响应")
        
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = self._extract_json(content)
            if not data.get("nodes"):
                logger.warning(f"GPT 响应 JSON 解析失败。原始响应: {content[:200]}")
        
        # 构建图
        graph = self._build_graph_from_response(data, context_label)
        
        logger.info(f"[GPT] 图构建完成: {len(graph.nodes)} 个节点, {len(graph.edges)} 条边")
        if len(graph.nodes) == 0:
            logger.warning(f"[GPT] 警告: 生成的图为空。原始数据: {data}")
        
        return graph
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取 JSON（备用方法）"""
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {"nodes": [], "edges": []}

    def _build_graph_from_response(self, data: Dict[str, Any], context_label: str) -> Graph:
        """从 GPT 响应构建图"""
        graph = Graph(graph_id="G_expansion")
        graph.source = "gpt_expander"
        graph._metadata.update({
            "context": context_label,
            "parent_node_id": data.get("parent_node_id"),
            "reason": data.get("reason")
        })
        
        node_map = {}
        
        # 处理节点
        nodes_data = data.get("nodes", [])
        for idx, node_data in enumerate(nodes_data):
            node_id = node_data.get("id", f"node_{idx}")
            label = node_data.get("label", node_data.get("name", f"节点_{idx}"))
            node_type_str = node_data.get("type", "system")
            
            node = Node(node_id=node_id, label=label)
            node.set_attr("node_type", node_type_str)
            node.set_state("expandable", True)
            
            # 存入元数据
            node.set_meta("source", "gpt")
            node.set_meta("description", node_data.get("description", ""))
            node.set_meta("original_type", node_type_str)
            
            graph.add_node(node)
            node_map[node_id] = node
        
        # 处理边
        edges_data = data.get("edges", [])
        for edge_data in edges_data:
            source_id = edge_data.get("source")
            target_id = edge_data.get("target")
            relation = edge_data.get("relation", "related_to")
            
            # 注意：source 可能是 parent_node_id（不在 node_map 中）
            # 这是正常的，因为它连接到原图的节点
            # 只添加至少有一个端点在当前增量图中的边
            if source_id in node_map or target_id in node_map:
                edge = Edge(
                    source=source_id,
                    target=target_id,
                    relation=relation,
                    metadata={"source": "gpt"}
                )
                # 使用 force=True 跳过节点存在性检查（因为 parent 节点不在这个图中）
                try:
                    graph.add_edge(edge)
                except ValueError:
                    # 如果验证失败，说明边连接到了外部节点（parent），这是预期的
                    # 我们仍然保存这条边，orchestrator 会在合并时处理
                    graph.edges.append(edge)
        
        return graph
