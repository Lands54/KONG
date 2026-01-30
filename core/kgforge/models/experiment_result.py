from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
from kgforge.models.graph import Graph

@dataclass
class ExperimentResult:
    """
    全量实验结果协议 (Pan-Graph Result Protocol)
    
    采用“容器-插槽”设计，编排器通过特定的接口（Method）向容器中填充数据，
    而不是直接操作内部字典，从而保证数据格式的一致性和未来扩展的兼容性。
    """
    # 最终产出的核心图对象（必填）
    graph: Graph
    
    # --- 内部存储桶 (不建议外部直接操作) ---
    _status: str = "running"
    _final_decision: Any = None
    _graphs: Dict[str, Graph] = field(default_factory=dict)
    _trace: List[Dict[str, Any]] = field(default_factory=list)
    _metrics: Dict[str, Any] = field(default_factory=dict)
    _metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # 默认记录开始时间
        self._metadata["start_timestamp"] = time.time()

    # --- 数据填报接口 (The Interfaces) ---

    def log_graph(self, stage_name: str, graph: Graph):
        """记录某个阶段的图快照或增量图"""
        self._graphs[stage_name] = graph

    def log_step(self, action: str, details: Optional[Dict[str, Any]] = None):
        """记录算法执行的一个步骤（追踪轨迹）"""
        entry = {
            "timestamp": time.time(),
            "action": action
        }
        if details:
            entry.update(details)
        self._trace.append(entry)

    def record_metric(self, key: str, value: Any):
        """记录一个量化指标"""
        self._metrics[key] = value

    def set_metadata(self, key: str, value: Any):
        """设置环境或上下文元数据"""
        self._metadata[key] = value

    def finish(self, final_decision: Any, success: bool = True):
        """标记实验完成并记录最终结论"""
        self._status = "success" if success else "failed"
        self._final_decision = final_decision
        self._metadata["end_timestamp"] = time.time()
        self._metadata["duration"] = self._metadata["end_timestamp"] - self._metadata["start_timestamp"]

    # --- 只读访问器 (Explicit Accessors) ---

    def status(self) -> str:
        return self._status

    def final_decision(self) -> Any:
        return self._final_decision

    def get_graphs(self) -> Dict[str, Graph]:
        return self._graphs

    def get_trace(self) -> List[Dict[str, Any]]:
        return self._trace

    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics

    def get_metadata(self) -> Dict[str, Any]:
        """获取全量元数据字典"""
        return self._metadata
        
    def meta(self, key: str, default: Any = None) -> Any:
        """获取特定元数据项"""
        return self._metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """将全量结果转化为字典，便于外层序列化"""
        return {
            "status": self._status,
            "final_decision": self._final_decision,
            "graphs": self._graphs,
            "trace": self._trace,
            "metrics": self._metrics,
            "metadata": self._metadata
        }
