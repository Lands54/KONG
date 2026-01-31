
import logging
import time
import pytest
from unittest.mock import MagicMock, patch
from python_service.core.logging import WebSocketLogHandler
from python_service.core.context import set_experiment_id, clear_experiment_id

def test_websocket_log_handler_emit():
    """Test that logs are queued and sent when experiment_id is set"""
    
    # Mock requests.post
    with patch("requests.post") as mock_post:
        handler = WebSocketLogHandler(node_url="http://test-node")
        logger = logging.getLogger("test_logger")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # 1. Test without experiment ID -> Should NOT send
        logger.info("Should not spy")
        time.sleep(0.1)
        mock_post.assert_not_called()
        
        # 2. Test with experiment ID -> Should send
        set_experiment_id("exp_123")
        logger.info("Hello World")
        
        # Wait for worker thread
        time.sleep(0.2)
        
        mock_post.assert_called()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://test-node/api/internal/log"
        assert kwargs["json"]["experimentId"] == "exp_123"
        assert kwargs["json"]["message"] == "Hello World"
        assert kwargs["json"]["level"] == "INFO"
        
        # Cleanup
        clear_experiment_id()

def test_websocket_log_handler_clears_context():
    """Test environment cleanup"""
    set_experiment_id("old_exp")
    clear_experiment_id()
    
    with patch("requests.post") as mock_post:
        handler = WebSocketLogHandler()
        logger = logging.getLogger("test_logger_2")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("No context")
        time.sleep(0.1)
        mock_post.assert_not_called()
