/**
 * Component and Orchestrator Type Definitions
 * 用于前端动态组件选择和配置
 */

export interface ParamSpec {
    type: 'string' | 'integer' | 'float' | 'boolean';
    default?: any;
    description?: string;
    enum?: string[];
    min?: number;
    max?: number;
}

export interface ComponentSpec {
    id: string;
    name: string;
    description: string;
    params: Record<string, ParamSpec>;
    class_path?: string;
}

export interface SlotRequirement {
    [slotName: string]: string;  // e.g. {"extractor": "IExtractor", "halting": "IHalting"}
}

export interface OrchestratorSpec extends ComponentSpec {
    slots: SlotRequirement;
}

export interface ComponentCatalog {
    [category: string]: any; // 支持动态类别如 calculators, testers 等
    extractors: ComponentSpec[];
    expanders: ComponentSpec[];
    fusions: ComponentSpec[];
    processors: ComponentSpec[];
    haltings: ComponentSpec[];
    orchestrators: OrchestratorSpec[];
}

export interface ExperimentConfig {
    orchestrator: string;
    components: Record<string, string>;  // slot name -> component id mapping
    params: Record<string, any>;
}

export interface NodeMetadata {
    status?: 'HALT-ACCEPT' | 'HALT-DROP' | 'LOOP' | 'HITL' | 'UNKNOWN';
    ablation_value?: number;
    uncertainty?: number;
    confidence?: number;
    structural_importance?: number;
    semantic_consistency?: number;
    halt_reason?: string;
    [key: string]: any;
}

export interface GraphNode {
    id: string;
    label: string;

    // Slots
    attributes: Record<string, any>;
    metrics: Record<string, number>;
    state: Record<string, any>;

    // 兼容层 (Optional, for existing components)
    node_type?: string;
    expandable?: boolean;
    metadata?: NodeMetadata;
}

export interface GraphEdge {
    source: string;
    target: string;

    // Slots
    attributes: Record<string, any>;
    metrics: Record<string, number>;

    // 兼容层
    relation: string;
    weight?: number;
}

export interface Graph {
    graph_id: string;
    nodes: Record<string, GraphNode>;
    edges: GraphEdge[];
}

export interface TraceEntry {
    iteration?: number;
    action?: string;
    metadata?: Record<string, any>;
    timestamp?: string;
}

export interface ExperimentResult {
    status: string;
    graph: Graph;
    intermediate_graphs: Record<string, Graph>;
    trace: TraceEntry[];
    metrics: Record<string, any>;
    metadata: Record<string, any>;
}
