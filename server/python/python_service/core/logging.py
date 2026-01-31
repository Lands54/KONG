import logging
import requests
import os
import threading
from queue import Queue
from python_service.core.context import get_experiment_id

class WebSocketLogHandler(logging.Handler):
    """
    Log handler that forwards logs to Node.js backend for WebSocket broadcasting.
    Uses a background thread to avoid blocking the main execution.
    """
    def __init__(self, node_url: str = None):
        super().__init__()
        # Ensure we don't start multiple threads if handler is re-initialized
        self.node_url = node_url or os.getenv("NODE_API_URL", "http://localhost:3000")
        self.endpoint = f"{self.node_url}/api/internal/log"
        self.queue = Queue()
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def emit(self, record):
        exp_id = get_experiment_id()
        if not exp_id:
            return
        
        try:
            msg = self.format(record)
            self.queue.put({
                "experimentId": exp_id,
                "message": msg,
                "level": record.levelname,
                "timestamp": record.created
            })
        except Exception:
            self.handleError(record)

    def _worker(self):
        while True:
            try:
                payload = self.queue.get()
                requests.post(self.endpoint, json=payload, timeout=1.0)
                self.queue.task_done()
            except Exception:
                # Log error locally or ignore
                pass
