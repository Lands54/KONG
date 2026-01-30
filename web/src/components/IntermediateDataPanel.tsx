import React from 'react';

interface IntermediateDataPanelProps {
  intermediateStats?: {
    [key: string]: {
      node_count?: number;
      edge_count?: number;
      depth?: number;
      source?: string;
    };
  };
}

export default function IntermediateDataPanel({ intermediateStats }: IntermediateDataPanelProps) {
  if (!intermediateStats || Object.keys(intermediateStats).length === 0) {
    return (
      <div style={{ padding: '12px', backgroundColor: '#fef3c7', borderRadius: '6px', fontSize: '11px', border: '1px solid #fcd34d' }}>
        <div style={{ fontWeight: 800, color: '#92400e', marginBottom: '4px' }}>TELEMETRY_OFFLINE</div>
        <div style={{ color: '#b45309', lineHeight: 1.4 }}>
          System awaiting data broadcast. Ensure orchestrator is active.
        </div>
      </div>
    );
  }

  const DataRow = ({ label, value }: { label: string, value: any }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '11px' }}>
      <span style={{ color: '#94a3b8', fontWeight: 600 }}>{label}</span>
      <span style={{ color: '#475569', fontFamily: 'monospace' }}>{value}</span>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {Object.entries(intermediateStats).map(([key, stats]) => (
        <div key={key} style={{
          padding: '12px',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '6px'
        }}>
          <div style={{
            fontSize: '10px',
            fontWeight: 800,
            color: '#1e293b',
            letterSpacing: '0.05em',
            marginBottom: '8px',
            borderBottom: '1px solid #cbd5e1',
            paddingBottom: '4px'
          }}>
            BUCKET::{key}
          </div>
          <DataRow label="NODES" value={stats.node_count || 0} />
          <DataRow label="EDGES" value={stats.edge_count || 0} />
          <DataRow label="DEPTH" value={stats.depth || 0} />
          <DataRow label="SOURCE" value={(stats.source || 'unknown').toUpperCase()} />
        </div>
      ))}

      {intermediateStats.G_B && intermediateStats.G_T && intermediateStats.G_F && (
        <div style={{
          marginTop: '8px',
          padding: '12px',
          backgroundColor: '#1e293b',
          borderRadius: '6px',
          color: '#fff'
        }}>
          <div style={{ fontSize: '10px', fontWeight: 800, opacity: 0.5, marginBottom: '8px' }}>DATA_CONVERGENCE_RATIO</div>
          <div style={{ fontSize: '18px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>{intermediateStats.G_B.node_count}</span>
            <span style={{ opacity: 0.3, fontSize: '12px' }}>+</span>
            <span>{intermediateStats.G_T.node_count}</span>
            <span style={{ opacity: 0.3, fontSize: '12px' }}>→</span>
            <span style={{ color: '#10b981' }}>{intermediateStats.G_F.node_count}</span>
          </div>
          <div style={{ fontSize: '9px', opacity: 0.5, marginTop: '4px' }}>UNITS: DISCOVERED_ENTITIES</div>
        </div>
      )}
    </div>
  );
}
