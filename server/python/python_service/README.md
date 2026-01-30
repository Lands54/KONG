# ⚡ Python Inference Service

This service provides a high-performance, production-ready FastAPI wrapper around the `dynhalting` research engine. It handles model management, component assembly, and asynchronous inference.

## 🏗 Key Features

- **Runtime Factory**: Dynamically assembles Orchestrators and Components based on API requests or configuration files.
- **Model Warmer**: Pre-loads heavy models (REBEL, Sentence-Transformers, LLM clients) during startup to ensure sub-second response times for subsequent calls.
- **Schema Validation**: Uses Pydantic to ensure strict data integrity between the frontend, Node.js backend, and the Python engine.
- **Lazy Loading**: Only imports heavy dependencies (like `torch` or `transformers`) when specifically required by a component.

## 🔌 API Endpoints

- **`POST /api/v1/infer`**: The main research interface.
  - Input: `goal`, `text`, `halting_strategy`, `max_depth`, etc.
  - Output: Full `ExperimentResult` including final graph, traces, and node-level halting metadata.
- **`GET /api/v1/health`**: Service status and model readiness.
- **`GET /api/v1/config/modules`**: List all available "slots" and their parameters.

## 🛠 Usage

### Starting the Service
```bash
# From project root
export PYTHONPATH=$PYTHONPATH:.
python backend/python_service/main.py
```

### Environment Variables
- `OPENROUTER_API_KEY`: Required for LLM-based expansion.
- `CUDA_VISIBLE_DEVICES`: (Optional) For REBEL/Embedding acceleration.

## 🧪 Implementation Detail: The Factory Pattern

The service uses `OrchestratorFactory` to build the "Motherboard". You can request custom configurations via the `params` field in the inference request:
```json
{
  "goal": "Explain the cooling system",
  "text": "...",
  "halting_strategy": "ASI",
  "max_depth": 5
}
```
The factory will automatically look up the `ASI_Strategy` from the module registry and inject it into the orchestrator.

---

*Note: This service is designed to be stateless. All experiment data is returned in the response or logged to the persistent Node.js backend.*
