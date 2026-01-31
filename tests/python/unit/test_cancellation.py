
import threading
import time
import pytest
from unittest.mock import MagicMock, patch
from kgforge.components.base import BaseOrchestrator, TaskCancelledError
from python_service.services.inference import InferenceEngine, CANCELLATION_EVENTS

class DummyOrchestrator(BaseOrchestrator):
    name = "dummy_for_cancel"
    
    @classmethod
    def get_required_slots(cls):
        return {}

    def run(self, **kwargs):
        # Simulate long running task
        for i in range(5):
            self.check_cancellation()
            time.sleep(0.1)
        return "finished"

def test_base_orchestrator_cancellation():
    """Test that BaseOrchestrator raises TaskCancelledError when event is set"""
    orch = DummyOrchestrator()
    event = threading.Event()
    orch.set_cancellation_event(event)

    # Should not raise yet
    orch.check_cancellation()

    # Set event
    event.set()
    
    with pytest.raises(TaskCancelledError):
        orch.check_cancellation()

def test_inference_engine_cancellation_flow():
    """Test full cancellation flow via InferenceEngine"""
    engine = InferenceEngine()
    experiment_id = "test_exp_123"
    
    # Mock UnifiedFactory to return our DummyOrchestrator
    with patch("python_service.services.inference.UnifiedFactory") as mock_factory:
        mock_orch = DummyOrchestrator()
        mock_factory.create_component.return_value = mock_orch
        
        # Start task in a separate thread
        def run_task():
            try:
                engine.run_dynamic(
                    goal="g", 
                    text="t", 
                    orchestrator="dummy_for_cancel", 
                    experiment_id=experiment_id
                )
            except TaskCancelledError:
                pass
            except Exception as e:
                print(f"Caught unexpected: {e}")

        t = threading.Thread(target=run_task)
        t.start()
        
        # Wait for task to start and register event
        time.sleep(0.1)
        assert experiment_id in CANCELLATION_EVENTS
        
        # Cancel it
        result = engine.cancel_task(experiment_id)
        assert result is True
        assert CANCELLATION_EVENTS[experiment_id].is_set()
        
        # Wait for thread to finish (should be fast due to cancel)
        t.join(timeout=1.0)
        assert not t.is_alive()
        
        # Cleanup check
        assert experiment_id not in CANCELLATION_EVENTS
