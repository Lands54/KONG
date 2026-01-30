"""
模拟 API 响应数据
"""

MOCK_GPT_RESPONSE = {
    "nodes": [
        {"id": "t1", "label": "Task 1", "type": "concept"},
        {"id": "t2", "label": "Task 2", "type": "concept"}
    ],
    "edges": [
        {"source": "t1", "target": "t2", "relation": "depends_on"}
    ]
}

MOCK_REBEL_TRIPLES = [
    ("United States", "capital", "Washington D.C.", 1.0),
    ("Joe Biden", "president_of", "United States", 1.0)
]
