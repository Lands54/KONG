# ⚒️ KGForge (KONG Graph Forge): The Universal Research Engine

`KGForge` is the algorithmic foundation of the KONG platform. It provides a standardized environment for implementing, observing, and orchestrating graph-based reasoning algorithms.

## 🏗 Philosophy: Component-Agnostic Platforms

KGForge treats research algorithms as **Pluggable Orchestrators**. It does not dictate the goal of your research (e.g., whether it's for knowledge extraction, multi-agent debate, or risk analysis). Instead, it provides the "Motherboard" where different components can be slotted in.

### 1. The Motherboard & Slots (Protocols)
Defined in `core/kgforge/protocols/`:
- **Universal Slots**: Standard interfaces for common operations like `IExtractor` (Parsing), `IExpander` (Generation), and `IFusion` (De-duplication).
- **Extensible Logic**: Developers can define NEW protocols that the platform will automatically recognize and render.

### 2. Standardized Data Infrastructure
KGForge provides a robust, research-grade data model (`core/kgforge/models/`):
- **`GraphElement` (Node/Edge)**: Features a unique **Slot Protocol** (`_attrs`, `_metrics`, `_state`, `_metadata`) to prevent data pollution.
- **`Execution Status`**: A first-class citizen in the platform, allowing any component to signal its lifecycle state (e.g., `PROCESSING`, `TERMINATED`, `ACTION_REQUIRED`) which is automatically handled by the observation layer.
- **`ExperimentResult`**: A high-fidelity container for tracing every decision, metric, and graph state change during execution.

## 🔌 Using the Platform

### Strategy 1: Ready-to-use Orchestrators
KGForge ships with reference implementations (like `DynamicHaltingOrchestrator`) that demonstrate how to use multiple components in a closed-loop reasoning process.

### Strategy 2: Custom Algorithm Development
To build a new reasoning system:
1. **Define your Protocol**: Create an interface in `protocols`.
2. **Implement your Components**: Add classes in `components`.
3. **Orchestrate**: Create an `Orchestrator` to define the high-level logic.

## 🎨 Observability: From Data to Vision
The platform is designed for **Data-Driven Visualization**. By setting standard visual hints (like `color`, `borderColor`, or `opacity`) on any node or edge, the platform's UI will automatically reflect the state of your algorithm without requiring you to write a single line of frontend code.

---

*KGForge is built for researchers who want to focus on 'The Algorithm', not the boilerplate.*
