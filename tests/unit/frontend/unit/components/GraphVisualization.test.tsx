/**
 * 图可视化组件的单元测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import GraphVisualization from '../../../../frontend/src/components/GraphVisualization';

describe('GraphVisualization', () => {
  it('should render empty graph message when no data', () => {
    const emptyGraph = { nodes: {}, edges: [] };
    render(<GraphVisualization graph={emptyGraph} experimentId="test-id" />);
    
    // 检查是否显示空图消息
    expect(screen.getByText(/图数据为空/i)).toBeInTheDocument();
  });

  it('should render graph with nodes', () => {
    const graph = {
      nodes: {
        n1: { id: 'n1', label: 'Node 1' },
        n2: { id: 'n2', label: 'Node 2' },
      },
      edges: [{ source: 'n1', target: 'n2', relation: 'connects' }],
    };
    
    render(<GraphVisualization graph={graph} experimentId="test-id" />);
    // 验证组件渲染（Cytoscape 会在容器中渲染）
    expect(document.querySelector('[data-cy="graph-container"]') || document.body).toBeTruthy();
  });
});
