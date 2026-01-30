import pytest
from kgforge.models.graph import Node
from kgforge.components.processors.utils.semantic_deduplicator import SemanticDeduplicator

def test_semantic_deduplicator_logic():
    """测试语义去重器的核心逻辑"""
    # 修正参数名为 similarity_threshold
    deduper = SemanticDeduplicator(similarity_threshold=0.5) 
    
    nodes = [
        Node(node_id="n1", label="The United States of America"),
        Node(node_id="n2", label="USA"),
        Node(node_id="n3", label="Banana")
    ]
    
    # 验证 embedding 计算
    embeddings = deduper.compute_embeddings(nodes)
    assert len(embeddings) == 3
    assert "n1" in embeddings
    
    # 验证相似对查找
    pairs = deduper.find_similar_pairs(nodes, embeddings)
    
    found = False
    for n_a_id, n_b_id, score in pairs:
        if (n_a_id == "n1" and n_b_id == "n2") or (n_a_id == "n2" and n_b_id == "n1"):
            found = True
            break
    assert found is True
