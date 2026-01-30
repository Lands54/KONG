# 🧠 dynhalting: The Core Research Engine

`dynhalting` is the algorithmic heart of the KONG workstation. it implements the **Dynamic Halting Loop**, a recursive process of graph construction, fusion, and evaluation.

## 🛠 Architecture: The Motherboard & Slots

The engine follows a strict **Interface Segregation** principle. The central orchestrator acts as a "Motherboard," providing slots for various functional components.

### 1. The Slots (Protocols)
Defined in `dynhalting/protocols/interfaces.py`:
- **`IExtractor`**: Bottom-Up evidence extraction (e.g., REBEL, OpenIE).
- **`IExpander`**: Top-Down goal decomposition (e.g., GPT-4, Llama-3).
- **`IFusion`**: Semantic alignment and graph merging.
- **`IHaltingStrategy`**: Value-based decision making.

### 2. The Components
Located in `dynhalting/components/`:
- **`extractors/`**: REBEL-based triplet extraction from raw text.
- **`expanders/`**: LLM-driven recursive goal expansion.
- **`fusions/`**: Semantic deduplication and node alignment using embeddings.
- **`halting/`**: Advanced halting strategies including ASI (Ablation-based), PSG, SCD, and UCB.

### 3. The Orchestrator (Motherboard)
- **`DynamicHaltingOrchestrator`**: The primary implementation of the research loop. It coordinates the data flow:
  1. `Extractor` -> $G_{Bottom-Up}$
  2. `Expander` -> $G_{Top-Down}$
  3. `Fusion`($G_{B}$, $G_{T}$) -> $G_{Fused}$
  4. `Halting`($G_{F}$) -> Decide (Loop/Halt/Drop/HITL)

## 📊 Data Models: Recursive System Graph

KONG uses a specialized graph model (`dynhalting/models/graph.py`) designed for research:
- **`Node`**: Contains rich metadata, including `ablation_value`, `uncertainty`, and `confidence`. Supports recursive `subgraph` references.
- **`Edge`**: Semantic relations with weights and evidence mapping.
- **`ExperimentResult`**: A comprehensive container for traces, metrics, and snapshots of every iteration.

## ⚙️ Advanced Halting Strategies

The new halting architecture supports **Node-Level Evaluation**:
- **ASI (Ablation-based Structural Importance)**: Estimates node value by simulating its removal from the system.
- **PSG (Probabilistic Subgraph)**: Evaluates the probability of a node being part of the "ground truth" ontology.
- **SCD (Semantic Consistency Degradation)**: Detects when additional information stops contributing to semantic clarity.
- **UCB (Upper Confidence Bound)**: Balances exploration of new nodes with exploitation of known high-value structures.

---

*For developers: To extend KONG, implement a new component class and ensure it inherits from the appropriate Protocol. Use the `ComponentManager` for registration.*
