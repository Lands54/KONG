from contextvars import ContextVar
from typing import Optional

# Context variable to store the current experiment ID
experiment_id_ctx: ContextVar[Optional[str]] = ContextVar("experiment_id", default=None)

def set_experiment_id(exp_id: str):
    experiment_id_ctx.set(exp_id)

def get_experiment_id() -> Optional[str]:
    return experiment_id_ctx.get()

def clear_experiment_id():
    experiment_id_ctx.set(None)
