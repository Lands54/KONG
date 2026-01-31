from contextvars import ContextVar
from typing import Optional

# Context variable to store the current experiment ID
experiment_id_ctx: ContextVar[Optional[str]] = ContextVar("experiment_id", default=None)
# Context variable to store intermediate statistics for the current experiment
current_stats_ctx: ContextVar[Optional[dict]] = ContextVar("current_stats", default=None)
# Context variable to store logs for the current experiment
current_logs_ctx: ContextVar[Optional[list]] = ContextVar("current_logs", default=None)

def set_experiment_id(exp_id: str):
    experiment_id_ctx.set(exp_id)
    current_stats_ctx.set({}) # Initialize empty stats
    current_logs_ctx.set([]) # Initialize empty logs

def get_experiment_id() -> Optional[str]:
    return experiment_id_ctx.get()

def clear_experiment_id():
    experiment_id_ctx.set(None)
    current_stats_ctx.set(None)
    current_logs_ctx.set(None)

def update_current_stats(new_stats: dict):
    stats = current_stats_ctx.get()
    if stats is not None:
        stats.update(new_stats)

def get_current_stats() -> dict:
    return current_stats_ctx.get() or {}

def append_current_log(log_entry: dict):
    logs = current_logs_ctx.get()
    if logs is not None:
        logs.append(log_entry)

def get_current_logs() -> list:
    return current_logs_ctx.get() or []
