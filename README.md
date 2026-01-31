# 🦍 PRISM (Platform for Reasoning, Inference, and Semantic Modeling)

> **面向大语言模型 (LLM) 的多样化科研实验平台**
> *A Diverse Research Platform for LLM Reasoning & Knowledge Engineering.*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Research%20Preview-orange)](https://github.com/your-repo)

**PRISM** 不仅仅是一个知识图谱构建工具，它是一个**开放的科研实验平台**。旨在填补非结构化文本、大语言模型 (LLM) 与结构化知识推理之间的鸿沟。

与传统的单一任务框架不同，PRISM 提供了一个高度灵活的**动态决策环境**。它天然支持 **"Think-on-Graph"**、迭代式扩展 (Iterative Expansion) 和多模式编排。无论是动态判停 (Dynamic Halting)、多智能体辩论 (Multi-Agent Debate) 还是混合推理路径研究，PRISM 都能为您提供一个开箱即用、高度可观测的实验底座。

---

## 🌟 核心特性 (Key Features)

### 1. 🧠 动态编排 (Dynamic Orchestration)
告别死板的 `Extract -> Store` 流程。PRISM 引入了 **Orchestrator** 概念，允许自定义复杂的推理循环：
*   **Top-Down**: 目标驱动的图扩展 (Expander)。
*   **Bottom-Up**: 基于文本的知识抽取 (Extractor)。
*   **Hybrid**: 混合编排，支持动态判停和自我修正。

### 2. 🎨 元数据驱动 UI (Metadata-Driven UI)
**后端改算法，前端零代码。**
PRISM 采用先进的协议自省机制。Python 后端定义的组件参数 (Schema) 会自动映射为 React 前端的动态表单。研究人员在调整算法超参数（如 `temperature`, `threshold`）时，无需触碰任何前端代码。

### 3. 🔬 科研级可观测性 (Research-Grade Observability)
*   **时光倒流**: 完整记录推理的每一步 (Trace) 和中间图状态 (Intermediate Graphs)，前端支持回放。
*   **影子实例**: 采用 "Shadow Instance" 模式隔离并发请求，确保不同实验参数互不干扰。
*   **数据透视**: 自动记录 Token 消耗、延迟和自定义 Metric。

### 4. 🔌 极致且插拔 (Plug-and-Play)
想要测试一个新的 Prompt 策略？或者接入一个新的 LLM？
只需继承 `BaseExpander` 并实现两个方法，文件保存即生效。系统会自动发现并注册你的新组件。

### 5. ⚡️ v3.0 高能特性 (New in v3.0)
*   **PRISM CLI (运维利器)**: 提供类似手术刀般的终端控制能力。支持原子化测试 (`test`)、无头实验执行 (`run`) 和实时日志追踪 (`logs`)。
*   **热重载引擎 (Hot-Reloading)**: 实现了 Python 核心组件的“保存即生效”。修改抽取/编排算法时，无需重启后端服务。
*   **健壮性架构 (Robustness)**: 具备全局错误传播机制（401/429错误穿透）、Prisma 数据库事务支持，以及 WebSocket 连接的自动断线重连（指数退避策略）。

---

## 🛠 开发工具: PRISM CLI

为了提升研发效率，我们提供了强大的终端工具集。您可以在不启动前端的情况下进行算法验证。

```bash
# 1. 诊断环境
./scripts/prism doctor

# 2. 列出所有注册组件
./scripts/prism ls

# 3. 原子测试单个组件 (智能自动转换 JSON/Graph 类型)
echo "文本输入" | ./scripts/prism test <component_id> --method extract

# 4. 无头运行完整实验管线
./scripts/prism run pipeline_config.json --dev

# 5. 实时追踪服务端日志
./scripts/prism logs -f
```

👉 **[查看完整 CLI 使用指南](docs/CLI_GUIDE.md)**

---

## 🏗 系统架构 (Architecture)

PRISM 采用现代化的分层架构，确保灵活性与性能的平衡。

![System Architecture](doc/architecture/kong_system_architecture_diagram_1769748943601.png)

*   **Frontend**: React + TypeScript，负责可视化与交互。
*   **Middleware**: Node.js (Express)，负责任务调度与数据持久化 (SQLite)。
*   **Backend**: Python (FastAPI)，核心推理引擎。
*   **Kernel**: KGForge，算法与组件协议库。

👉 **[查看完整架构文档 (Architecture Deep Dive)](doc/architecture/GLOBAL.md)**

---

## 📚 文档中心 (Documentation)

所有的技术细节、接口定义和开发指南都已整理至 `doc/` 目录：

| 文档 | 描述 | 受众 |
| :--- | :--- | :--- |
| **[架构全景图 (Global)](doc/architecture/GLOBAL.md)** | C4 模型视角下的系统全貌与核心决策 | **必读** |
| **[CLI 使用指南 (CLI)](docs/CLI_GUIDE.md)** | 如何使用 PRISM CLI 进行高效运维与测试 | **推荐** |
| **[开发者指南 (Guide)](doc/architecture/DEVELOPER_GUIDE.md)** | 手把手教你编写 Expander/Orchestrator | **开发者** |
| **[v3.0 路线图 (Roadmap)](docs/ver3.md)** | 系统的演进方向、热重载与健壮性设计 | 架构师 |
| **[核心库设计 (Core)](doc/architecture/CORE.md)** | Python Engine 的内部实现机制 | 架构师 |
| **[接口协议文档 (Protocol)](doc/architecture/NODE.md)** | 前后端交互的 Pan-Graph Result 协议 | 前后端 |

---

## 🚀 快速开始 (Quick Start)

### 前置要求
*   Python 3.10+
*   Node.js 18+
*   NPM / Yarn

### 1. 安装依赖

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装前端依赖
cd web && npm install

# 3. 安装 Node 中间层依赖
cd ../server/node && npm install
cd ../..
```

### 2. 配置环境 (Critical)

在项目根目录创建 `.env` 文件（参考 `.env.example`）：

```bash
# OpenRouter API Key (必需，用于 GPT 扩展器)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx

# 可选：配置基础模型
DEFAULT_MODEL=openai/gpt-4-turbo
```

> ⚠️ **注意**: 请确保您的 API Key 有效且所在网络环境支持访问该 API 服务。

### 3. 一键启动

```bash
./start.sh
```

服务将运行在以下端口：
*   **Web Console**: [http://localhost:3000](http://localhost:3000)
*   **Node API**: [http://localhost:3001](http://localhost:3001)
*   **Python Engine**: [http://localhost:8000](http://localhost:8000)

---

## 🛠 扩展指南 (Contributing)

PRISM 提供了极致的扩展能力，**甚至支持自定义全新的组件类型**（如Validators, Summarizers），且**无需修改前端代码**。

1.  **添加组件 (Add Component)**: 在 `core/kgforge/components/<category>/modules/` 下新建 `.py` 文件，继承对应基类。
2.  **添加类型 (Add Type)**: 在 `core/kgforge/protocols/interfaces.py` 中定义新的 Interface，系统会自动扫描并分类。

重启服务后，**Web 控制台会自动渲染出新类型和新组件的配置界面**。

详细教程请参阅 [Developer Guide](doc/architecture/DEVELOPER_GUIDE.md)。

---

## 📄 许可证 (License)

本项目采用 **MIT License** 开源。
Copyright © 2024-2026 PRISM Research Team.
