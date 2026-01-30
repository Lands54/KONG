"""
语义去重模块 (Core Implementation)
使用 sentence-transformers 计算节点 embedding
对相似度高于阈值的节点进行合并
纯粹的业务逻辑类，不依赖系统协议
"""

from typing import List, Dict, Tuple, Set, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from kgforge.models import Graph, Node
from kgforge.utils import get_logger

logger = get_logger(__name__)

class SemanticDeduplicator:
    """语义去重器核心逻辑"""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        similarity_threshold: float = 0.9,
        device: str = None,
        **kwargs
    ):
        """
        初始化语义去重器
        
        Args:
            model_name: sentence-transformers 模型名称
            similarity_threshold: 相似度阈值（默认 0.9）
            device: 设备（None 自动选择）
        """
        self.model_name = model_name
        self.threshold = similarity_threshold
        self.device = device
        self.model = None
        self._initialized = False
    
    def load_model(self):
        """延迟加载模型"""
        if self._initialized:
            return
        
        try:
            logger.info(f"正在加载 embedding 模型: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self._initialized = True
            logger.info("Embedding 模型加载完成")
        except Exception as e:
            error_msg = (
                f"Embedding 模型加载失败: {e}\n"
                f"请检查网络连接和磁盘空间后重试"
            )
            # raise RuntimeError(error_msg) from e
            logger.error(error_msg)
            raise e
    
    def compute_embeddings(self, nodes: List[Node]) -> Dict[str, np.ndarray]:
        """计算节点的 embedding"""
        if not self._initialized:
            self.load_model()
        
        # 提取节点标签 (使用新接口)
        texts = [node.attr("label") for node in nodes]
        
        if not texts:
            return {}

        # 计算 embedding
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # 构建映射
        result = {}
        for node, embedding in zip(nodes, embeddings):
            node.set_attr("embedding", embedding.tolist())  # 保存到属性插槽
            result[node.id] = embedding
        
        return result

    def find_similar_pairs(
        self,
        nodes: List[Node],
        embeddings: Dict[str, np.ndarray]
    ) -> List[Tuple[str, str, float]]:
        """找到相似节点对"""
        if not nodes or not embeddings:
            return []

        similar_pairs = []
        node_ids = [node.id for node in nodes]
        embedding_matrix = np.array([embeddings[nid] for nid in node_ids])
        
        if len(embedding_matrix) == 0:
            return []

        similarity_matrix = cosine_similarity(embedding_matrix)
        
        for i, node_id1 in enumerate(node_ids):
            for j, node_id2 in enumerate(node_ids[i+1:], start=i+1):
                similarity = similarity_matrix[i, j]
                if similarity >= self.threshold:
                    similar_pairs.append((node_id1, node_id2, float(similarity)))
        
        return similar_pairs

    def merge_similar_nodes(
        self,
        graph: Graph,
        similar_pairs: List[Tuple[str, str, float]]
    ) -> Tuple[Graph, Dict[str, str]]:
        """合并相似节点 (原地修改)"""
        merge_map = {}
        
        for node_id1, node_id2, _ in similar_pairs:
            if node_id1 < node_id2:
                target, source = node_id1, node_id2
            else:
                target, source = node_id2, node_id1
            
            while source in merge_map: source = merge_map[source]
            while target in merge_map: target = merge_map[target]
            if source != target: merge_map[source] = target
        
        for source_id, target_id in merge_map.items():
            if source_id in graph.nodes and target_id in graph.nodes:
                graph.merge_node(source_id, target_id)
                target_node = graph.get_node(target_id)
                if target_node:
                    target_node.set_attr("canonical_id", target_id)
        
        for node in graph.nodes.values():
            if not node.attr("canonical_id"):
                node.set_attr("canonical_id", node.id)
        
        return graph, merge_map
    
    def deduplicate(self, graph: Graph) -> Tuple[Graph, Dict[str, str]]:
        """对图进行语义去重"""
        nodes = list(graph.nodes.values())
        if len(nodes) == 0:
            return graph
        
        # 计算 embedding
        embeddings = self.compute_embeddings(nodes)
        
        # 找到相似对
        similar_pairs = self.find_similar_pairs(nodes, embeddings)
        
        
        id_mapping = {}
        # 合并相似节点
        if similar_pairs:
            logger.info(f"发现 {len(similar_pairs)} 对相似节点（阈值={self.threshold}）")
            graph, id_mapping = self.merge_similar_nodes(graph, similar_pairs)
        else:
            # logger.debug("未发现相似节点")
            pass
        
        return graph, id_mapping
