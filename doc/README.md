# PRISM (Platform for Reasoning, Inference, and Semantic Modeling) Documentation

欢迎阅读 PRISM 项目文档。本项目旨在构建一个**动态、可解释、高并发**的大语言模型推理研究框架。

## 🏛 架构概览 (Architecture)

1.  **[System Architecture (Global)](./architecture/GLOBAL.md)**
    *   **必读**。系统的全景图，包含 C4 模型图解和核心技术决策。建议所有新加入的同学先阅读此文档。

2.  **[Frontend Architecture](./architecture/FRONTEND.md)**
    *   Web 控制台 (React) 的设计文档。
    *   重点解释了 *Metadata-Driven UI* 和 *Slot-Based Config*。

3.  **[Node Middleware Architecture](./architecture/NODE.md)**
    *   Node.js 服务的职责说明。
    *   重点解释了 *Data Steward* 角色和 *EAV Data Persistence*。

4.  **[Core Library Architecture](./architecture/CORE.md)**
    *   Python 内核 (KGForge) 的设计文档。
    *   解释了 *Shadow Instances* 并发模型和 *Pan-Graph Protocol*。

---

## 👩‍💻 开发者指南 (Developer Guide)

*   **[Component Development Guide](./architecture/DEVELOPER_GUIDE.md)**
    *   **算法工程师必读**。
    *   如何编写新的 Orchestrator / Expander / Extractor？
    *   如何使用 Logger 和 Profiler 进行调试？
    *   Graph 数据结构操作手册。

## 📂 历史文档 (Legacy)

*   [Legacy Design v1](./architecture/legacy_design_v1.md): 项目初期的设计草案（已归档）。
