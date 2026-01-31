import logging
import requests
import os
import threading
from queue import Queue
from python_service.core.context import get_experiment_id

class StreamingEventHandler(logging.Handler):
    """
    流式事件处理器
    将日志和结构化遥测数据转发给 Node.js 后端进行 WebSocket 广播。
    统一使用 /api/internal/telemetry 接口。
    """
    def __init__(self, node_url: str = None):
        super().__init__()
        self.node_url = node_url or os.getenv("NODE_API_URL", "http://localhost:3000")
        self.endpoint = f"{self.node_url}/api/internal/telemetry"
        self.queue = Queue()
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def emit(self, record):
        exp_id = get_experiment_id()
        if not exp_id:
            return
        
        try:
            # 基础 Payload
            payload = {
                "experimentId": exp_id,
                "timestamp": record.created
            }

            # 检查是否包含遥测数据 (通过 extra={"telemetry": ...} 传入)
            if hasattr(record, "telemetry"):
                payload["type"] = "TELEMETRY"
                payload["payload"] = record.telemetry
            else:
                # 默认为普通文本日志
                payload["type"] = "LOG"
                log_data = {
                    "message": self.format(record),
                    "level": record.levelname,
                    "timestamp": record.created
                }
                payload["payload"] = log_data
                
                # 持久化日志到 Context
                try:
                     from python_service.core.context import append_current_log
                     append_current_log(log_data)
                except ImportError:
                    pass

            self.queue.put(payload)
        except Exception:
            self.handleError(record)

    def _worker(self):
        while True:
            try:
                payload = self.queue.get()
                requests.post(self.endpoint, json=payload, timeout=1.0)
                self.queue.task_done()
            except Exception:
                # 如果连接失败，静默忽略以避免影响主线程
                pass
