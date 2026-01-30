/**
 * 图数据转换
 * 将后端 JSON 转换为 Cytoscape 格式
 * 处理父子节点关系（复合节点）
 */

export function graphToCytoscape(graph: any): any[] {
  if (!graph || !graph.nodes) {
    return [];
  }

  const elements: any[] = [];

  // 添加节点
  Object.values(graph.nodes).forEach((node: any) => {
    // 基础插槽 (Element-Slot Container Pattern)
    const attributes = node.attributes || {};
    const metrics = node.metrics || {};
    const state = node.state || {};
    const metadata = node.metadata || {};

    // 状态优先级：顶层 > state.status > attributes.status > metadata.status
    const status = node.status || state.status || attributes.status || metadata.status || 'LOOP';

    const nodeData: any = {
      id: node.id,
      label: node.label || attributes.label || 'Unknown',
      status: status,

      // 保存完整数据槽，供详情面板使用
      attributes: attributes,
      metrics: metrics,
      state: state,
      metadata: metadata,

      // 提取核心指标给 Cytoscape 的样式映射（如节点颜色、工具提示）
      ablationValue: metrics.ablation_value ?? metadata.ablation_value,
      uncertainty: metrics.uncertainty ?? metadata.uncertainty,
      confidence: metrics.confidence ?? metadata.confidence,
      haltReason: state.halt_reason ?? metadata.halt_reason,
      source: node.source || state.source || metadata.source || 'unknown'
    };

    // 处理父节点（复合节点）
    if (node.parentNodeId) {
      nodeData.parent = node.parentNodeId;
    }

    elements.push({
      data: nodeData,
      group: 'nodes'
    });
  });

  // 添加边
  if (graph.edges && Array.isArray(graph.edges)) {
    graph.edges.forEach((edge: any) => {
      elements.push({
        data: {
          id: `${edge.source}-${edge.target}-${edge.relation}`,
          source: edge.source,
          target: edge.target,
          relation: edge.relation || '',
          attributes: edge.attributes || {},
          metrics: edge.metrics || {},
          metadata: edge.metadata || {}
        },
        group: 'edges'
      });
    });
  }

  return elements;
}
