from enum import Enum
from dataclasses import dataclass

class HaltingDecision(Enum):
    """判停决策枚举"""
    HALT_ACCEPT = "HALT"       # 停止并接受
    HALT_DROP = "DROP"         # 停止并丢弃
    LOOP = "LOOP"              # 继续展开
    HITL = "HITL"              # 人类介入
    CONTINUE = "CONTINUE"      # 继续循环

@dataclass
class HaltingResponse:
    """判停模型响应"""
    decision: HaltingDecision
    reason: str = ""

class HaltingMode(Enum):
    """判停模式"""
    ALWAYS_LOOP = "always_loop"
    ALWAYS_HALT = "always_halt"
    RULE_BASED = "rule_based"
    STRATEGY = "strategy"
