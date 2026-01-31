# PRISM v3.0 Roadmap & Manifesto

> **Theme**: From Prototype to Platform —— Robustness, Agility, and Developer Experience.

## 1. Context & Status Quo (v2.0-rc)
We have successfully transitioned the project from a specific research tool (`KONG`) to a universal, component-agnostic platform (`PRISM`). 

### Achievements in v2.0
- **KGForge Universalization**: The core engine is now generic, with no hardcoded assumptions about "Halting" or specific states effectively decoupling logic from the platform.
- **Data-Driven Visualization**: Frontend visuals are purely driven by backend data slots (Attributes, Metrics, State), enabling "Backend-Only" UI updates.
- **Brand Identity**: Established the `PRISM` (Platform for Reasoning, Inference, and Semantic Modeling) identity with a new logo and consistent naming convention.

### Current Pain Points
Despite these architectural wins, the *Developer Experience (DX)* and *Operational Stability* remain at a "Research Protestotype" level:
1.  **Fragility**: Errors (e.g., API limits, network drops) often result in silent failures or generic "Error" states.
2.  **Slow Iteration**: Modifying a single line of component code requires a full server restart (FastAPI + Node).
3.  **Heavy Operations**: Simple tasks like rerunning an experiment or checking component status require navigating a heavy Web UI.

---

## 2. Design Philosophy: The "Developer-First" Platform

For v3.0, we shift our focus from "What can it run?" to **"How well can we build on it?"**.

> **"A robust nervous system, a live laboratory, and a surgical scalpel."**

### Core Pillars

1.  **Robustness (The Nervous System)**
    *   **Philosophy**: The system must have "pain receptors." Errors should be structured, propagated, and visible, not swallowed.
    *   **Goal**: Atomicity in data persistence and resilience in network communication.

2.  **Hot-Reloading (The Live Laboratory)**
    *   **Philosophy**: "Code, Save, Retry." The loop should be instantaneous.
    *   **Goal**: Zero-restart updates for `KGForge` components.

3.  **PRISM CLI (The Surgical Scalpel)**
    *   **Philosophy**: GUI is for observation; CLI is for operation.
    *   **Goal**: A lightweight command-line interface for rapid execution, debugging, and system diagnostics.

---

## 3. v3.0 Implementation Plan

### Phase 1: Robustness & Resilience (The "Safety Net")
- [x] **Error Propagation System**:
    - Define granular `PrismError` codes (e.g., `AUTH_FAILED`, `RATE_LIMIT`).
    - Ensure errors penetrate from Python -> Node -> UI with full fidelity.
- [x] **Bug Fixes**:
    - Fixed broken import paths in `inference.py` and `routes.py`.
- [x] **Transaction Integrity**:
    - Use Prisma transactions to ensure `ExperimentData` is saved atomically.
- [x] **Connection Resilience**:
    - Implement "Heartbeat & Reconnect" logic for WebSockets.

### Phase 2: Hot-Reloading Engine (The "Speed Boost")
- [x] **Component Watcher**:
    - built a `watchdog` service monitoring `core/kgforge/components`.
- [x] **Module Eviction Logic**:
    - Smart handling of `sys.modules` to force Python to reload modified logic without restarting the process.
- [x] **Registry Sync**:
    - Auto-update the `UnifiedFactory` registry when a component file is touched.

### Phase 3: PRISM CLI (The "Dev Console")
- [x] **`prism` Command**:
    - `prism ls`: List active components and slots.
    - `prism run/rerun`: Execute experiments headlessly.
    - `prism doctor`: Self-diagnose environment health.
    - `prism test`: **[NEW]** Atomic component testing with hot-reload workflow.
- [x] **Log Streaming**:
    - `prism logs -f <id>`: Real-time telemetry in the terminal.

---

## 4. Handover Notes for Next Agent

**Identity**: You are inheriting the **PRISM** project at the dawn of its v3.0 evolution.
**Immediate Priority**: Architecture over Features. Do not add new extractors or models yet. Focus on the *infrastructure* that makes adding them easy.

**Key Technical Constraints**:
- **Do not revert** the platform-agnostic nature of `KGForge`.
- **Do not hardcode** "Halting" logic back into the core.
- **Maintain** the strict "Slot Protocol" for all data flow.

*Let's make PRISM the standard for Agentic research.*
