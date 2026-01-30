import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { graphToCytoscape } from '../services/graphTransformer';
import { useWebSocket } from '../hooks/useWebSocket';

// 注册 dagre 扩展
cytoscape.use(dagre);

interface GraphVisualizationProps {
  graph: any;
  experimentId: string;
  onNodeClick?: (node: any) => void;
}

type LayoutType = 'dagre' | 'breadthfirst' | 'grid' | 'circle' | 'concentric' | 'cose';

export default function GraphVisualization({ graph, experimentId, onNodeClick }: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const { lastMessage } = useWebSocket(experimentId);
  const [layoutType, setLayoutType] = useState<LayoutType>('dagre');

  useEffect(() => {
    if (!containerRef.current) return;

    // 先清除容器内容，确保之前的内容（包括提示信息）被清除
    containerRef.current.innerHTML = '';

    // 如果没有图数据，显示提示
    if (!graph || !graph.nodes || Object.keys(graph.nodes).length === 0) {
      containerRef.current.innerHTML = `
        <div style="padding: 40px; text-align: center; color: #666;">
          <div style="font-size: 48px; margin-bottom: 20px;">📊</div>
          <div style="font-size: 18px; font-weight: bold; margin-bottom: 10px;">图数据为空</div>
          <div style="font-size: 14px; color: #999; line-height: 1.8;">
            可能原因：<br/>
            • REBEL 未抽取到实体关系<br/>
            • GPT 未生成节点<br/>
            • 数据仍在处理中<br/>
            <br/>
            请检查 Python 服务日志获取详细信息
          </div>
        </div>
      `;
      return;
    }

    // 初始化 Cytoscape
    const elements = graphToCytoscape(graph);

    // 如果没有元素，显示提示
    if (elements.length === 0) {
      const nodeCount = Object.keys(graph.nodes).length;
      const edgeCount = graph.edges?.length || 0;
      containerRef.current.innerHTML = `
        <div style="padding: 60px; text-align: center; color: #94a3b8; font-family: 'SF Mono', monospace;">
          <div style="font-size: 32px; margin-bottom: 24px; opacity: 0.5;">[ NO_VISUALIZABLE_DATA ]</div>
          <div style="font-size: 11px; letter-spacing: 0.1em; line-height: 2;">
            NODES_DETECTED: ${nodeCount}<br/>
            EDGES_DETECTED: ${edgeCount}<br/>
            <br/>
            <span style="color: #64748b">REASON: SCHEMA_MISMATCH OR EMPTY_RESULT_SET</span>
          </div>
        </div>
      `;
      return;
    }

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'width': 'label',
            'height': 'label',
            'padding': '16px',
            'shape': 'roundrectangle',
            'background-color': '#ffffff',
            'border-width': 1,
            'border-color': '#cbd5e1',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-family': 'SF Mono, Monaco, Cascadia Code, monospace',
            'font-size': '12px',
            'font-weight': 700,
            'color': '#1e293b',
            'text-max-width': '120px',
            'text-wrap': 'wrap',
            'line-height': 1.4,
            'corner-radius': '4',
            'transition-property': 'background-color, border-color, border-width',
            'transition-duration': 150
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 2,
            'border-color': '#1e293b',
            'background-color': '#f1f5f9'
          }
        },
        {
          selector: 'node[status="HALT-ACCEPT"]',
          style: {
            'border-color': '#10b981',
            'border-width': 2,
            'background-color': '#f0fdf4'
          }
        },
        {
          selector: 'node[status="LOOP"]',
          style: {
            'border-color': '#f59e0b',
            'border-width': 2,
            'background-color': '#fffbeb'
          }
        },
        {
          selector: 'node[status="HALT-DROP"]',
          style: {
            'background-color': '#f8fafc',
            'border-color': '#cbd5e1',
            'color': '#94a3b8',
            'opacity': 0.6,
            'border-width': 1.5,
            'border-style': 'dashed'
          }
        },
        {
          selector: 'node[status="LOOP"]',
          style: {
            'background-color': '#ffffff',
            'border-color': '#e2e8f0',
            'border-width': 1.5
          }
        },
        {
          selector: 'node[status="HITL"]',
          style: {
            'background-color': '#fffbeb',
            'border-color': '#f59e0b',
            'border-width': 2,
            'color': '#92400e'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#cbd5e1',
            'target-arrow-color': '#cbd5e1',
            'target-arrow-shape': 'triangle-backcurve',
            'arrow-scale': 1.5,
            'curve-style': 'bezier',
            'control-point-step-size': 60,
            'label': 'data(relation)',
            'font-size': '11px',
            'font-family': 'Inter, system-ui',
            'font-weight': 500,
            'text-background-opacity': 1,
            'text-background-color': '#ffffff',
            'text-background-padding': '6px',
            'text-background-shape': 'roundrectangle',
            'text-rotation': 'autorotate',
            'color': '#475569',
            'opacity': 0.8,
            'target-distance-from-node': '4px',
            'source-distance-from-node': '4px'
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'width': 4,
            'line-color': '#6366f1',
            'target-arrow-color': '#6366f1',
            'opacity': 1
          }
        }
      ],
      layout: getLayoutConfig(layoutType)
    });

    // 为节点添加点击事件
    if (cyRef.current) {
      cyRef.current.on('tap', 'node', (evt) => {
        const node = evt.target;
        if (onNodeClick) {
          onNodeClick(node.data());
        }
      });

      // 鼠标悬停在节点上时显示手型
      cyRef.current.on('mouseover', 'node', () => {
        if (containerRef.current) containerRef.current.style.cursor = 'pointer';
      });

      cyRef.current.on('mouseout', 'node', () => {
        if (containerRef.current) containerRef.current.style.cursor = 'default';
      });
    }

    // 添加节点悬停事件，显示属性信息
    if (cyRef.current) {
      cyRef.current.on('mouseover', 'node', (evt: any) => {
        const node = evt.target;
        const data = node.data();
        const metadata = data.metadata || {};
        const attributes = data.attributes || {};
        const metrics = data.metrics || {};

        // 创建工具提示内容
        // 预定义字段的显示名称映射
        const fieldLabels: Record<string, string> = {
          status: '状态',
          ablation_value: '价值',
          uncertainty: '不确定性',
          confidence: '置信度',
          structural_importance: '结构重要性',
          semantic_consistency: '语义一致性',
          halt_reason: '原因',
          information_gain: '信息增益',
          expanded: '已展开',
          source: '来源'
        };

        // 格式化值的辅助函数
        const formatValue = (key: string, value: any): string => {
          if (value === null || value === undefined) return '';
          if (typeof value === 'number') {
            // 根据字段类型决定小数位数
            if (key.includes('value') || key.includes('importance') || key.includes('gain')) {
              return value.toFixed(3);
            } else if (key.includes('uncertainty') || key.includes('confidence') || key.includes('consistency')) {
              return value.toFixed(3);
            } else {
              return value.toFixed(2);
            }
          }
          if (typeof value === 'boolean') {
            return value ? '是' : '否';
          }
          if (typeof value === 'object') {
            return JSON.stringify(value); // 简化显示
          }
          return String(value);
        };

        // 构建主要属性显示（优先显示常用字段）
        const mainFields = ['status', 'ablation_value', 'uncertainty', 'confidence', 'structural_importance', 'semantic_consistency', 'halt_reason'];
        const mainContent = mainFields
          .filter(key => metadata[key] !== undefined && metadata[key] !== null)
          .map(key => {
            const label = fieldLabels[key] || key;
            const value = formatValue(key, metadata[key]);
            return `<div style="margin-bottom: 4px;"><strong style="color: #475569;">${label}:</strong> <span style="color: #1e293b;">${value}</span></div>`;
          })
          .join('');

        // 构建 Metrics 显示
        const metricsContent = Object.keys(metrics).length > 0
          ? `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0;">
              <div style="font-weight: 600; color: #64748b; font-size: 10px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">量化指标 (Metrics)</div>
              ${Object.entries(metrics).map(([key, value]) => {
            const label = fieldLabels[key] || key.replace(/_/g, ' ');
            return `<div style="margin-bottom: 3px; font-size: 10px;"><strong style="color: #94a3b8;">${label}:</strong> <span style="color: #64748b;">${formatValue(key, value)}</span></div>`;
          }).join('')}
            </div>`
          : '';

        // 构建 Attributes 显示
        const attrKeys = Object.keys(attributes).filter(k => k !== 'label' && k !== 'id'); // 过滤掉基础字段
        const attributesContent = attrKeys.length > 0
          ? `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0;">
              <div style="font-weight: 600; color: #64748b; font-size: 10px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">语义属性 (Attributes)</div>
              ${attrKeys.slice(0, 5).map(key => { // 限制显示数量，避免过长
            const label = key;
            const valStr = String(attributes[key]);
            const displayVal = valStr.length > 30 ? valStr.substring(0, 27) + '...' : valStr;
            return `<div style="margin-bottom: 3px; font-size: 10px;"><strong style="color: #94a3b8;">${label}:</strong> <span style="color: #64748b;">${displayVal}</span></div>`;
          }).join('')}
              ${attrKeys.length > 5 ? `<div style="font-size: 9px; color: #cbd5e1; margin-top: 2px;">+${attrKeys.length - 5} more...</div>` : ''}
            </div>`
          : '';

        // 构建其他 metadata 字段显示
        const otherFields = Object.keys(metadata).filter(key => !mainFields.includes(key));
        const otherContent = otherFields.length > 0
          ? `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0;">
              <div style="font-weight: 600; color: #64748b; font-size: 10px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">其他元数据</div>
              ${otherFields.map(key => {
            const label = fieldLabels[key] || key.replace(/_/g, ' ');
            const value = formatValue(key, metadata[key]);
            return `<div style="margin-bottom: 3px; font-size: 10px;"><strong style="color: #94a3b8;">${label}:</strong> <span style="color: #64748b;">${value}</span></div>`;
          }).join('')}
            </div>`
          : '';

        const tooltipContent = `
          <div style="padding: 12px; font-size: 12px; line-height: 1.8; min-width: 220px; max-width: 350px;">
            <div style="font-weight: 700; margin-bottom: 10px; color: #1e293b; font-size: 14px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
              ${data.label || data.id}
            </div>
            <div style="color: #64748b; font-size: 11px;">
              ${mainContent}
              ${metricsContent}
              ${attributesContent}
              ${otherContent}
            </div>
          </div>
        `;

        // 显示工具提示（使用简单的 DOM 元素）
        const tooltip = document.createElement('div');
        tooltip.innerHTML = tooltipContent;
        tooltip.style.position = 'absolute';
        tooltip.style.backgroundColor = 'rgba(255, 255, 255, 0.98)';
        tooltip.style.border = '1px solid #e2e8f0';
        tooltip.style.borderRadius = '8px';
        tooltip.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.zIndex = '1000';
        tooltip.id = 'node-tooltip';

        // 移除旧工具提示
        const existingTooltip = document.getElementById('node-tooltip');
        if (existingTooltip) {
          existingTooltip.remove();
        }

        document.body.appendChild(tooltip);

        // 更新位置
        const updateTooltipPosition = (e: MouseEvent) => {
          tooltip.style.left = `${e.clientX + 15}px`;
          tooltip.style.top = `${e.clientY + 15}px`;
        };

        const mouseMoveHandler = (e: MouseEvent) => updateTooltipPosition(e);
        document.addEventListener('mousemove', mouseMoveHandler);

        // 存储事件处理器以便清理
        (node as any)._tooltipHandler = mouseMoveHandler;
        (node as any)._tooltipElement = tooltip;

        // 初始位置
        const pos = node.renderedPosition();
        const container = cyRef.current!.container();
        const containerRect = container.getBoundingClientRect();
        tooltip.style.left = `${containerRect.left + pos.x + 15}px`;
        tooltip.style.top = `${containerRect.top + pos.y + 15}px`;
      });

      cyRef.current.on('mouseout', 'node', (evt: any) => {
        const node = evt.target;
        const tooltip = (node as any)._tooltipElement;
        const handler = (node as any)._tooltipHandler;

        if (tooltip) {
          tooltip.remove();
          (node as any)._tooltipElement = null;
        }
        if (handler) {
          document.removeEventListener('mousemove', handler);
          (node as any)._tooltipHandler = null;
        }
      });
    }

    return () => {
      // 清理所有工具提示
      const tooltips = document.querySelectorAll('#node-tooltip');
      tooltips.forEach(t => t.remove());

      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [graph, layoutType]);

  // 当布局类型改变时，重新应用布局
  useEffect(() => {
    if (!cyRef.current || !graph || !graph.nodes || Object.keys(graph.nodes).length === 0) return;

    try {
      const layout = cyRef.current.layout(getLayoutConfig(layoutType));
      layout.run();
    } catch (error) {
      console.error('Error applying layout:', error);
    }
  }, [layoutType, graph]);

  // 处理 WebSocket 更新
  useEffect(() => {
    if (!lastMessage || !cyRef.current) return;

    const data = JSON.parse(lastMessage.data);
    if (data.type === 'graph_update' && data.data) {
      const elements = graphToCytoscape(data.data);
      cyRef.current.json({ elements });
    }
  }, [lastMessage]);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
      {/* 布局选择器 - 现代设计 */}
      <div style={{
        padding: '12px 20px',
        borderBottom: '1px solid #e2e8f0',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            fontSize: '13px',
            fontWeight: 600,
            color: '#64748b',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Visualization Layout
          </span>
          <select
            value={layoutType}
            onChange={(e) => setLayoutType(e.target.value as LayoutType)}
            style={{
              padding: '6px 32px 6px 12px',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
              backgroundColor: 'white',
              color: '#334155',
              outline: 'none',
              appearance: 'none',
              backgroundImage: 'url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%2364748b\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3e%3cpolyline points=\'6 9 12 15 18 9\'%3e%3c/polyline%3e%3c/svg%3e")',
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 8px center',
              backgroundSize: '16px',
              transition: 'all 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#6366f1'}
            onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
          >
            <option value="dagre">Hierarchical (Dagre)</option>
            <option value="breadthfirst">Breadth First</option>
            <option value="cose">Force Directed (CoSE)</option>
            <option value="concentric">Concentric</option>
            <option value="circle">Circle</option>
            <option value="grid">Grid</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px', fontFamily: 'monospace' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: '#22c55e', border: '1px solid #166534' }}></div>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 500 }}>HALT-ACCEPT</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: '#cbd5e1', border: '1px dashed #94a3b8', opacity: 0.6 }}></div>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 500 }}>HALT-DROP</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: '#ffffff', border: '1.5px solid #e2e8f0' }}></div>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 500 }}>LOOP</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: '#fffbeb', border: '2px solid #f59e0b' }}></div>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 500 }}>HITL</span>
          </div>
        </div>
      </div>

      {/* 图形容器 */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          width: '100%',
          height: '100%',
          backgroundColor: '#f8fafc'
        }}
      />
    </div>
  );
}

/**
 * 获取布局配置
 */
function getLayoutConfig(layoutType: LayoutType): cytoscape.LayoutOptions {
  const baseConfig = {
    padding: 50,
    animate: true,
    animationDuration: 800,
    animationEasing: 'ease-in-out' as any
  };

  switch (layoutType) {
    case 'dagre':
      return {
        name: 'dagre',
        ...baseConfig,
        rankDir: 'TB',
        nodeSep: 70,
        edgeSep: 40,
        rankSep: 100,
        ranker: 'network-simplex',
        spacingFactor: 1.1
      } as any;

    case 'breadthfirst':
      return {
        name: 'breadthfirst',
        ...baseConfig,
        directed: true,
        spacingFactor: 1.5,
        avoidOverlap: true,
        roots: undefined // 自动选择根节点
      };

    case 'grid':
      return {
        name: 'grid',
        ...baseConfig,
        rows: undefined, // 自动计算
        cols: undefined, // 自动计算
        position: (node: any) => undefined // 自动定位
      };

    case 'circle':
      return {
        name: 'circle',
        ...baseConfig,
        radius: undefined, // 自动计算
        startAngle: 0,
        sweep: undefined, // 360度
        clockwise: true,
        sort: undefined // 按度排序
      };

    case 'concentric':
      return {
        name: 'concentric',
        ...baseConfig,
        minNodeSpacing: 50,
        height: undefined, // 自动计算
        width: undefined, // 自动计算
        equidistant: false,
        startAngle: 0,
        sweep: undefined,
        clockwise: true,
        sort: undefined
      };

    case 'cose':
      return {
        name: 'cose',
        ...baseConfig,
        quality: 'default', // 'default', 'draft'
        nodeDimensionsIncludeLabels: true,
        nodeRepulsion: 4500,
        idealEdgeLength: 50,
        edgeElasticity: 0.45,
        nestingFactor: 0.1,
        gravity: 0.25,
        numIter: 2500,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0
      };

    default:
      return {
        name: 'dagre',
        ...baseConfig
      } as any;
  }
}
