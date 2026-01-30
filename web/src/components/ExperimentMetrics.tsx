import React, { useEffect, useState } from 'react';
import { api } from '../services/apiClient';

interface ExperimentMetricsProps {
  experimentId: string;
  data?: any;
}

/**
 * 自适应实验指标面板
 * 会根据后端 Metrics 对象动态生成 UI 槽位
 */
export default function ExperimentMetrics({ experimentId, data }: ExperimentMetricsProps) {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // 基础标准指标（这些总是会被优先显示在顶部）
  const CORE_KEYS = ['nodeCount', 'edgeCount', 'iterations', 'avgDepth', 'total_nodes', 'total_edges'];

  useEffect(() => {
    if (data) {
      const allMetrics = {
        ...(data.metrics || {}),
        nodeCount: data.metadata?.node_count || (data.graph?.nodes ? Object.keys(data.graph.nodes).length : 0),
        edgeCount: data.metadata?.edge_count || (data.graph?.edges ? data.graph.edges.length : 0),
        iterations: data.metadata?.iterations || data.metrics?.total_iterations || 0,
      };
      setMetrics(allMetrics);
      setLoading(false);
    }
  }, [data]);

  useEffect(() => {
    if (!data) {
      api.experiments.metrics(experimentId)
        .then((resp: any) => {
          setMetrics(resp);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [experimentId, data]);

  if (loading) return <div style={{ fontSize: '11px', color: '#94a3b8' }}>SYNCING_METRICS...</div>;
  if (!metrics) return <div style={{ fontSize: '11px', color: '#94a3b8' }}>NO_METRICS_STREAM</div>;

  const formatKey = (key: string) => key.replace(/_/g, ' ').toUpperCase();

  const MetricItem = ({ label, value, color = '#1e293b' }: { label: string, value: any, color?: string }) => (
    <div style={{
      padding: '10px 0',
      borderBottom: '1px solid #f1f5f9',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <div style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.05em' }}>
        {formatKey(label)}
      </div>
      <div style={{ fontSize: '14px', fontWeight: 800, color: color, fontFamily: 'monospace' }}>
        {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(4)) : String(value)}
      </div>
    </div>
  );

  // 提取动态指标（排除掉核心指标和复杂对象）
  const dynamicEntries = Object.entries(metrics).filter(([key, val]) => {
    return !CORE_KEYS.includes(key) &&
      key !== 'decisionStats' &&
      typeof val !== 'object' &&
      val !== null;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Core Standard Metrics */}
      <div>
        <div style={{ fontSize: '9px', fontWeight: 900, color: '#cbd5e1', marginBottom: '8px' }}>[ STANDARD_STATS ]</div>
        <MetricItem label="SURFACE_NODES" value={metrics.nodeCount || metrics.total_nodes || 0} />
        <MetricItem label="LINKAGE_EDGES" value={metrics.edgeCount || metrics.total_edges || 0} />
        <MetricItem label="PROCESS_CYCLES" value={metrics.iterations || 0} />
      </div>

      {/* 2. Adaptive Extended Metrics (指标自适应区) */}
      {dynamicEntries.length > 0 && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f8fafc',
          borderRadius: '6px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ fontSize: '9px', fontWeight: 900, color: '#94a3b8', marginBottom: '8px' }}>[ EXTENDED_TELEMETRY ]</div>
          {dynamicEntries.map(([key, val]) => (
            <MetricItem key={key} label={key} value={val} color="#3b82f6" />
          ))}
        </div>
      )}

      {/* 3. Decision Probability Bars */}
      {metrics.decisionStats && Object.keys(metrics.decisionStats).length > 0 && (
        <div>
          <div style={{ fontSize: '9px', fontWeight: 900, color: '#cbd5e1', marginBottom: '12px' }}>[ DECISION_DISTRIBUTION ]</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(metrics.decisionStats).map(([decision, count]: [string, any]) => (
              <div key={decision}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', fontWeight: 700, marginBottom: '4px' }}>
                  <span style={{ color: '#475569' }}>{decision}</span>
                  <span style={{ color: '#94a3b8' }}>{count}</span>
                </div>
                <div style={{ height: '4px', backgroundColor: '#f1f5f9', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(100, (count / (metrics.nodeCount || 1)) * 100)}%`,
                    height: '100%',
                    backgroundColor: decision.includes('HALT') ? '#10b981' : '#3b82f6'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
