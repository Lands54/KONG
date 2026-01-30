# KONG Design System: Scientific Dashboard

## 1. Design Philosophy
The KONG frontend is designed to feel like a **High-Precision Scientific Instrument** (e.g., an oscilloscope, a flight controller, or an advanced IDE). Unlike traditional business applications that prioritize "friendliness" and "softness", KONG priorities **Data Density**, **Axiomatic Structure**, and **Cold Precision**.

## 2. Visual Core (The "DNA")

### 2.1 Typography
- **Core Font**: `SF Mono`, `Monaco`, `Cascadia Code`, `monospace`.
- **Rational**: Every character has fixed width, making numerical data perfectly aligned and structured.
- **Hierarchy**:
  - **Headings**: Semibold, high contrast, often used with `letter-spacing: 0.1em` and `text-transform: uppercase`.
  - **Labels**: Muted gray (`#94a3b8`), small font size (`10px-11px`).
  - **Values**: High contrast (`#1e293b`), monospace, prioritized for readability.

### 2.2 Elevation & Depth
- **Pattern**: Floating Cards.
- **Rules**: Components should not "split" the screen. They should float above the graph with clear margins (usually `20px`).
- **Shadows**: Multi-layered soft shadows to simulate ambient occlusion.
  - `boxShadow: '0 10px 30px rgba(0,0,0,0.15)'`
- **Corners**: `12px` or `16px` border-radius for a refined "industrial product" feel.

### 2.3 Color Coding (The Slot System)
Colors are assigned to functional data categories (Slots):
- **State (`#3b82f6` Blue)**: Running status, process control, lifecycle.
- **Metrics (`#8b5cf6` Purple)**: Computed values, confidence, ablation scores.
- **Attributes (`#10b981` Green)**: Semantic labels, extraction results, fixed properties.
- **Metadata (`#94a3b8` Gray)**: Traceability info, system logs, auxiliary data.

## 3. Component Standards

### 3.1 The Data Item (List View)
Every piece of data should be presented as a "List Item" in a high-density table:
- **Left**: Muted uppercase label.
- **Middle**: Discreet dotted or solid separator.
- **Right**: High-contrast, aligned value.

### 3.2 Navigation & Controls
- **Transparency**: Use blurry backdrops (`backdrop-filter: blur(8px)`) for control bars.
- **Minimalism**: No heavy borders. Use light gray (`#f1f5f9`) or semi-transparent divisions.

## 4. Interaction Principle
"Details on Demand".
- The **Graph** is the primary "Ocean of Data".
- The **Floating Panels** (like NodeMetadataPanel) are the "Microscopes" used to inspect specific elements without losing context.
