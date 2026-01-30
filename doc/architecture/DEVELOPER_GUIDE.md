# KGForge 开发者指南 (Developer Guide)

本文档旨在为 KGForge 组件开发者提供关于**日志记录**、**数据监测**、**指标统计**及**调试工具**的标准接口使用指南。遵循本指南可确保您的组件与 KONG 系统的其他部分（如前端可视化、遥测系统）无缝集成。

## 1. 日志与调试 (Logging & Debugging)

### 1.1 标准日志 (Standard Logging)
**原则**：禁止在组件代码中使用 `print()`。必须使用系统提供的 `logger` 以确保日志能被正确收集、分级和持久化。

**使用方法**：
```python
from kgforge.utils import get_logger

# 在模块顶部获取 logger
logger = get_logger(__name__)

class MyComponent:
    def run(self, input_data):
        logger.info(f"开始处理数据: {len(input_data)} 条")
        
        try:
            # 业务逻辑...
            logger.debug("处理细节: ...")
        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
```

*   **INFO**: 关键流程节点（如：开始扩展、图构建完成）。
*   **DEBUG**: 调试细节（如：生成的 Prompt 长度、中间变量值）。
*   **ERROR**: 异常情况。

### 1.2 数据快照 (Data Profiler)
**原则**：当需要记录**复杂结构数据**（如大段 Prompt、API 原始 JSON 响应、大型 Graph 对象）用于离线排查问题时，使用 `profiler`。

**使用方法**：
```python
from kgforge.utils import profiler

# 记录 API 原始响应
profiler.record("api_response_raw", response_json, sub_dir="my_module/responses")

# 记录生成的 Prompt (方便检查 Prompt Engineering 效果)
profiler.record("generated_prompt", prompt_string, extension="txt")
```
*   **存储位置**：默认位于项目根目录 `logs/debug_snapshots/`。
*   **文件名**：系统会自动添加毫秒级时间戳前缀，防止覆盖。

---

## 2. 实验结果与指标 (Results & Metrics)

编排器 (Orchestrator) 负责产出 `ExperimentResult` 对象。为了支持前端的**全过程回溯**和**可视化**，请务必使用以下标准接口填充数据。

### 2.1 核心对象
```python
from kgforge.models.experiment_result import ExperimentResult

# 初始化
result = ExperimentResult(graph=initial_graph)
```

### 2.2 记录量化指标 (Metrics)
用于记录数值型指标，前端可在“Metrics”面板中展示。

```python
# 记录 Token 消耗
result.record_metric("total_tokens", 1500)

# 记录置信度分数
result.record_metric("confidence_score", 0.95)

# 记录耗时 (自动计算的 duration 除外)
result.record_metric("llm_latency_ms", 450)
```

### 2.3 记录执行轨迹 (Trace)
用于记录算法的决策过程，前端以时间轴形式展示。

```python
result.log_step(
    action="EXPAND_NODE", 
    details={
        "node_id": "concept_abc", 
        "strategy": "bfs",
        "reason": "High uncertainty"
    }
)
```

### 2.4 记录中间图 (Intermediate Graphs)
用于记录算法关键阶段的图状态，支持前端“时光倒流”查看每一步的图结构。

```python
# 记录第一阶段后的图状态
result.log_graph("after_initial_expansion", current_graph_snapshot)

# 记录融合后的图
result.log_graph("after_fusion", fused_graph)
```

---

## 3. 图处理工具 (Graph Utilities)

### 3.1 快速统计
在开发过程中，如果想快速查看图的基本信息：

```python
from kgforge.utils import print_graph_summary

# 打印节点数、边数、深度及前5个节点示例
print_graph_summary(my_graph, title="融合后图状态")
```

---

## 4. 最佳实践清单 (Checklist)

开发新组件时，请自检：
- [ ] 是否使用了 `get_logger` 而不是 `print`？
- [ ] 关键数据是否通过 `profiler` 留档（如果需要调试）？
- [ ] (编排器) 是否通过 `result.log_step` 描述了执行动作？
- [ ] (编排器) 是否记录了关键的中间图状态 (`log_graph`)？
- [ ] (编排器) 是否输出了量化指标 (`record_metric`)？

---

## 5. 数据结构操作 (Data Structures)

KGForge 采用 **Slot-based** 设计模式，所有图元素（Node, Edge）都继承自 `GraphElement`，拥有四个标准数据插槽：
1.  **Attributes** (特征): 静态属性（如 label, relation）。
2.  **Metrics** (指标): 量化数值（如 weight, confidence）。
3.  **State** (状态): 流程控制标记（如 expansion_count）。
4.  **Meta** (元数据): 溯源信息（如 source_model）。

### 5.1 创建节点 (Node)
```python
from kgforge.models.graph import Node

# 基础创建
node = Node(node_id="concept_nlp", label="Natural Language Processing")

# 使用插槽填充数据
node.set_attr("category", "Technology") \
    .set_metric("importance", 0.95) \
    .set_state("processed", False)

# 访问数据
print(node.attr("label"))       # "Natural Language Processing"
print(node.metric("importance")) # 0.95
```

### 5.2 创建边 (Edge)
```python
from kgforge.models.graph import Edge

# 基础创建 (Directed: Source -> Target)
edge = Edge(source="concept_nlp", target="concept_ai", relation="part_of")

# 添加权重和元数据
edge.set_metric("weight", 0.8) \
    .set_meta("extractor", "rebel-large")
```

### 5.3 操作图 (Graph)
`Graph` 是节点的容器，同时维护拓扑结构。

```python
from kgforge.models.graph import Graph

# 初始化
graph = Graph(graph_id="subgraph_01")
graph.source = "gpt-4-turbo"

# 添加元素
graph.add_node(node)
graph.add_edge(edge)

# 拓扑查询
neighbors = graph.get_neighbors("concept_nlp")  # ["concept_ai"]
degree = graph.get_node_degree("concept_nlp")   # 1

# 序列化 (用于传输或保存)
data_dict = graph.to_dict()
```

---

## 6. 组件扩展指南 (Component Extension Guide)

KONG 采用 **插件化架构**，所有算法模块（Orchestrator, Expander, Extractor 等）均可热插拔。新增一个组件只需遵循以下“四步走”流程。

### 6.1 步聚一：确定组件类型与位置
根据功能选择基类和目录：

| 组件类型 | 基类 | 目录位置 | 职责 |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | `BaseOrchestrator` | `core/kgforge/components/orchestrators/modules/` | 顶层循环逻辑，控制推理流程 |
| **Expander** | `BaseExpander` | `core/kgforge/components/expanders/modules/` | 节点生成/展开 (Node Generation) |
| **Extractor** | `BaseExtractor` | `core/kgforge/components/extractors/modules/` | 关系抽取 (Relation Extraction) |
| **Fusion** | `BaseFusion` | `core/kgforge/components/fusions/modules/` | 图融合与去重 (Graph Merge) |

### 6.2 步骤二：继承与初始化
创建一个新的 `.py` 文件，继承对应基类。

*注意：必须在 `__init__` 中正确合并配置。*

```python
# core/kgforge/components/expanders/modules/my_expander.py
from typing import Dict, Any
from kgforge.components.base import BaseExpander

class MyCustomExpander(BaseExpander):
    name = "my_custom"  # 内部 ID
    display_name = "我的自定义展开器" # 友好显示名

    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        # 1. 规范化参数合并
        mapped_config = (config or {}).copy()
        mapped_config.update(kwargs)
        
        # 2. 调用父类初始化
        # 这会将 mapped_config 绑定到 self.config
        super().__init__(mapped_config)
        
        # 3. 初始化私有属性
        self.threshold = self.config.get("threshold", 0.5)
```

### 6.3 步骤三：定义自描述元数据 (Critical!)
这是 KONG **元数据驱动 UI** 的核心。你在这里定义的 schema 会自动变成前端的滑块和输入框。

**必须实现 `@classmethod get_component_spec`**

```python
    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {
            "id": "my_custom",
            "name": "My Custom Expander",
            "description": "Uses a heuristic algorithm to expand nodes.",
            "params": {
                # 定义参数: 这会在前端生成一个 0.0-1.0 的滑块
                "threshold": {
                    "type": "number",
                    "default": 0.5,
                    "description": "Confidence Threshold",
                    "min": 0.0,
                    "max": 1.0
                },
                # 定义参数: 这会在前端生成一个下拉框
                "mode": {
                    "type": "string",
                    "default": "fast",
                    "description": "Execution Mode",
                    "enum": ["fast", "accurate"]
                }
            },
            # 如果你的组件依赖其他组件 (如 Orchestrator 依赖 Expander)
            "slots": {
                # "inner_model": "IModel" 
            }
        }
```

### 6.4 步骤四：实现核心逻辑
实现接口规定的核心方法（如 `expand_goal`, `run`, `extract` 等）。

```python
    def expand_goal(self, goal: str, **kwargs) -> Graph:
        # 1. 获取 logger
        from kgforge.utils import get_logger
        logger = get_logger(__name__)
        
        logger.info(f"Expanding goal: {goal}")
        
        # 2. 业务逻辑 (创建图)
        from kgforge.models import Graph, Node
        g = Graph()
        node = Node(node_id="n1", label=f"Expanded: {goal}")
        g.add_node(node)
        
        return g
```

### 6.5 自动发现
KONG Server 启动时会自动扫描 `modules` 目录。
1.  保存你的 `.py` 文件。
2.  运行 `./start.sh` 重启服务。
3.  刷新 Web 控制台，你的新组件就会出现在列表中，参数面板也会自动生成。

---

## 7. 增加新的组件类型 (New Component Type Guide)

如果你需要的不仅仅是增加一个新的 Expander（实现），而是想引入一种全新的组件类型（例如 `Validator` 或 `Summarizer`），步骤会稍微多一些，但依然不需要修改 Server 核心代码。

### 7.1 步骤一：创建类型目录
在 `core/kgforge/components/` 下创建新目录：

```bash
core/kgforge/components/
├── validators/          # <--- 新建目录
│   ├── __init__.py
│   └── modules/         # <--- 存放具体实现
│       └── __init__.py
```

### 7.2 步骤二：定义基类 (Interface)
在 `core/kgforge/components/validators/__init__.py` 中定义抽象基类。

*必须在类文档字符串中声明 interface tag，例如 `[Component Interface: IValidator]`*，这有助于自省机制识别。

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseValidator(ABC):
    """
    [Component Interface: IValidator]
    验证器基类：用于对图结构的合法性进行校验
    """
    
    name: str = "base_validator"
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def validate(self, graph) -> bool:
        pass
        
    @classmethod
    def get_component_spec(cls) -> Dict[str, Any]:
        return {}
```

### 7.3 步骤三：注册组件类型 (Enable Discovery)
KONG 的组件发现通过协议反射机制实现。为了让系统识别新的 "validator" 类型，你必须在协议层注册它。

文件：`core/kgforge/protocols/interfaces.py`

在文件末尾添加你的新接口定义：

```python
class IValidator(IDescribable, ABC):
    """验证器协议"""
    category = "validators"  # <--- 这就是分类标识符
    
    @abstractmethod
    def validate(self, graph: Any, **kwargs) -> Any:
        pass
```

*这就够了！* `engine.py` 会自动扫描 `interfaces.py` 中的所有子类，发现 `category="validators"` 后，下次扫描 `kgforge.components` 时就会自动寻找实现了 `IValidator` 的类。无需修改 `engine.py` 里的任何代码。

### 总结
1.  **新增实现 (Impl)**：只需放文件，无需注册（已有类型）。
2.  **新增类型 (Type)**：需创建目录 -> 定义基类 -> 在 `interfaces.py` 注册协议。 KONG 会全自动处理剩下的事情（扫描、分类、前端渲染）。


