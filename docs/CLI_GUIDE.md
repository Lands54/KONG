# 🛠️ PRISM CLI User Guide

*The Surgical Scalpel for your Knowledge Graph Platform.*

The **PRISM CLI** is a terminal-based interface designed for rapid component testing, system diagnosis, and experiment verification. It is built to bypass the heavy Web UI, allowing for instant feedback loops during development.

---

## 🚀 Getting Started

Ensure you are in the project root. The CLI wrapper is located at `./scripts/prism`.

```bash
# Verify installation
./scripts/prism --help
```

---

## 🔍 System Diagnosis (`doctor`)

Before running experiments, always ensure your environment is healthy.

```bash
./scripts/prism doctor
```

**Checks Performed:**
- ✅ Project Root Integrity
- ✅ Core Module (`kgforge`) Presence
- ✅ `.env` Configuration
- ✅ Critical Python Dependencies

---

## 📋 Component Listing (`ls`)

View all registered components in your system. This command introspects the codebase dynamically.

```bash
# List everything
./scripts/prism ls

# Filter by category
./scripts/prism ls -c extractors
./scripts/prism ls -c orchestrators
```

**Columns:**
- **Category**: Component type (extractor, fusion, etc.)
- **ID**: The unique string ID used in pipelines.
- **Class Path**: The Python class backing the component.
- **Capabilities**: Features like `(Preload)` or `(Configurable)`.

---

## ⚡ Atomic Testing (`test`)

The most powerful command. Instantiate and run a single component in isolation.

### 1. Basic Usage
If a component is callable (has `__call__`), you can run it directly:

```bash
./scripts/prism test <COMPONENT_ID> --input "Your input text"
```

### 2. Explicit Method Selection
If a component uses a specific method name (e.g., `extract`, `expand`), you must specify it:

```bash
./scripts/prism test rebel --input "Apple is a fruit" --method extract
```

### 3. Unix Piping (`|`)
Chain inputs from other commands. The CLI automatically detects `stdin`.

```bash
echo "Hello World" | ./scripts/prism test rebel --method extract --json
```

### 4. Smart Casting (The Magic 🪄)
The CLI inspects the Python type hints of the target method.
- If the method expects a **`Graph` object**, and you pass **JSON**, the CLI automagically converts it.
- If the method expects a **`Dict`**, it parses the JSON string.

**Example: Testing a Strategy that needs a Graph**
```bash
# 1. Provide JSON representing a graph
echo '{"nodes": [{"id": "n1"}], "edges": []}' > graph.json

# 2. Pipe it into the component
cat graph.json | ./scripts/prism test ASI_Strategy --method decide
```

### 5. Parameter Injection
Override component configuration using JSON parameters:

```bash
./scripts/prism test example_generator --params '{"seed": 42}' --input "start"
```

---

## 🏗️ Experiment Execution (`run` & `rerun`)

Run full pipelines headlessly without the browser.

### `prism run <config.json>`
Execute a new pipeline from a local configuration file.

**Example `config.json`:**
```json
{
    "orchestrator_id": "complex_example",
    "components": {
        "extractor": "example_generator"
    },
    "text": "Start simulation",
    "goal": "Generate data"
}
```

```bash
./scripts/prism run config.json --dev
```

### `prism rerun <EXT_ID>`
Re-execute a historical experiment by fetching its configuration from the running server.

```bash
# Requires localhost:8000 to be running
./scripts/prism rerun exp_123456 --dev
```

---

## 📡 Telemetry (`logs`)

Stream logs from the running Python service directly to your terminal.

```bash
# Show last 50 lines (snapshot)
./scripts/prism logs

# Follow existing logs (tail -f)
./scripts/prism logs -f

# Show last 100 lines and follow
./scripts/prism logs -n 100 -f
```

---

## 🐛 Troubleshooting

**"Error: Component does not have method '...'"**
- Cause: You didn't specify `--method` and the object isn't callable.
- Fix: The error message lists available public methods. Pick one and use `--method <name>`.

**"Traceback (execution failed)"**
- Cause: The component code threw an exception.
- Fix: Use the pretty-printed traceback (powered by `Rich`) to locate the exact line in your component code.

---

*PRISM CLI v1.0 - Built on Typer & Rich*
