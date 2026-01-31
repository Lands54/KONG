import React, { useState } from 'react';

interface NodeMetadataPanelProps {
    node: {
        id: string;
        label: string;
        node_type?: string;
        metadata?: any;
        attributes?: Record<string, any>;
        metrics?: Record<string, any>;
        state?: Record<string, any>;
        status?: string;
    } | null;
    onClose: () => void;
}

/**
 * 科学实验风格的节点元数据面板
 * 采用列表化、高信息密度的展示方式
 */
export default function NodeMetadataPanel({ node, onClose }: NodeMetadataPanelProps) {
    const [activeTab, setActiveTab] = useState<'all' | 'metrics' | 'attributes' | 'state'>('all');
    const [showRaw, setShowRaw] = useState(false);

    if (!node) return null;

    const attributes = node.attributes || {};
    const metrics = node.metrics || {};
    const state = node.state || {};
    const metadata = node.metadata || {};

    // 状态标签样式
    const getStatusStyle = (status: string = 'UNKNOWN') => {
        const colors: Record<string, { bg: string; text: string }> = {
            'HALT-ACCEPT': { bg: '#d1fae5', text: '#065f46' },
            'HALT-DROP': { bg: '#fee2e2', text: '#991b1b' },
            'LOOP': { bg: '#fef3c7', text: '#92400e' },
            'HITL': { bg: '#dbeafe', text: '#1e40af' },
            'UNKNOWN': { bg: '#f3f4f6', text: '#374151' }
        };
        return colors[status] || colors['UNKNOWN'];
    };

    const statusObj = getStatusStyle(node.status);

    // 数据列表条目
    const DataItem = ({ label, value, isRaw = false }: { label: string, value: any, isRaw?: boolean }) => (
        <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            padding: '8px 0',
            borderBottom: '1px solid #f1f5f9',
            fontSize: '13px',
            opacity: isRaw ? 0.7 : 1,
            backgroundColor: isRaw ? '#fff7ed' : 'transparent'
        }}>
            <span style={{ color: isRaw ? '#ea580c' : '#64748b', fontWeight: isRaw ? 600 : 500 }}>
                {isRaw ? `[DEV] ${label}` : label}
            </span>
            <span style={{
                color: '#334155',
                textAlign: 'right',
                wordBreak: 'break-all',
                maxWidth: '60%',
                fontFamily: 'monospace'
            }}>
                {typeof value === 'object' ? JSON.stringify(value) :
                    (typeof value === 'number' ? value.toFixed(4).replace(/\.?0+$/, '') : String(value))}
            </span>
        </div>
    );

    // 渲染分段
    const renderSection = (title: string, data: Record<string, any>, icon: string, color: string = '#64748b') => {
        const internalBlacklist = new Set(['label', 'enriched', 'enrich_ts', 'id', 'node_id', 'attributes', 'metadata', 'state', 'metrics']);

        const entries = Object.entries(data).filter(([k, v]) => {
            if (v === undefined || v === null) return false;
            // 如果不是 DEV 模式，执行严格过滤
            if (!showRaw) {
                if (k.startsWith('_') || internalBlacklist.has(k)) return false;
                if (typeof v === 'object' && Object.keys(v).length === 0) return false;
                if ((k === 'attributes' || k === 'metadata' || k === 'state' || k === 'metrics') && typeof v === 'object') return false;
            }
            return true;
        });

        if (entries.length === 0) return null;

        return (
            <div style={{ marginBottom: '20px' }}>
                <h4 style={{
                    fontSize: '11px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    color: color,
                    marginBottom: '8px',
                    paddingBottom: '4px',
                    borderBottom: `1px solid ${color}33`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                }}>
                    <span>{icon}</span> {title}
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    {entries.map(([key, val]) => (
                        <DataItem key={key} label={key} value={val} isRaw={showRaw && (key.startsWith('_') || internalBlacklist.has(key))} />
                    ))}
                </div>
            </div>
        );
    };

    const sectionColors = {
        state: '#3b82f6',
        metrics: '#8b5cf6',
        attributes: '#10b981',
        metadata: '#94a3b8'
    };

    return (
        <div style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            bottom: '20px',
            width: '420px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1000,
            border: showRaw ? '2px solid #ea580c' : '1px solid #cbd5e1',
            fontFamily: 'SF Mono, Monaco, Cascadia Code, monospace',
            overflow: 'hidden',
            transition: 'all 0.2s'
        }}>
            {/* Minimal Header */}
            <div style={{
                padding: '16px 20px',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: showRaw ? '#fff7ed' : '#f1f5f9'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: statusObj.bg === '#f3f4f6' ? '#64748b' : statusObj.text }}></div>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>{node.label}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button
                        onClick={() => setShowRaw(!showRaw)}
                        style={{
                            border: showRaw ? '1px solid #ea580c' : '1px solid #94a3b8',
                            background: showRaw ? '#ea580c' : 'transparent',
                            color: showRaw ? 'white' : '#64748b',
                            borderRadius: '4px',
                            padding: '2px 8px',
                            fontSize: '10px',
                            fontWeight: 800,
                            cursor: 'pointer',
                            letterSpacing: '0.05em'
                        }}
                    >
                        {showRaw ? '[DEV_ON]' : '[DEV_OFF]'}
                    </button>
                    <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: '18px', color: '#94a3b8' }}>✕</button>
                </div>
            </div>

            {/* Scientific List View */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                {showRaw && (
                    <div style={{
                        backgroundColor: '#fff7ed',
                        border: '1px solid #ffedd5',
                        padding: '12px',
                        borderRadius: '6px',
                        marginBottom: '20px',
                        fontSize: '11px',
                        color: '#9a3412',
                        lineHeight: '1.4'
                    }}>
                        <strong>DEBUG_OVERRIDE_ACTIVE:</strong> Showing raw internal data structures and technical flags.
                    </div>
                )}
                {/* Status as a List Item First */}
                <div style={{ marginBottom: '24px', backgroundColor: '#f8fafc', padding: '10px', borderRadius: '6px' }}>
                    <DataItem label="EXEC_STATUS" value={node.status || 'UNKNOWN'} />
                    <DataItem label="NODE_ID" value={node.id} />
                </div>

                {renderSection('Lifecycle State', state, '⬢', sectionColors.state)}
                {renderSection('Computed Metrics', metrics, '📊', sectionColors.metrics)}
                {renderSection('Semantic Attributes', attributes, '🧬', sectionColors.attributes)}

                {/* Legacy Data - 仅显示尚未被分类的原始数据 */}
                {(() => {
                    const slottedKeys = new Set([
                        ...Object.keys(state),
                        ...Object.keys(metrics),
                        ...Object.keys(attributes)
                    ]);
                    const filteredMetadata = Object.fromEntries(
                        Object.entries(metadata).filter(([k]) => !slottedKeys.has(k))
                    );
                    return renderSection('Raw Metadata (Trace)', filteredMetadata, '⌥', sectionColors.metadata);
                })()}
            </div>

            <div style={{ padding: '10px', backgroundColor: '#f8fafc', fontSize: '9px', color: '#94a3b8', textAlign: 'center', borderTop: '1px solid #f1f5f9' }}>
                PAN_GRAPH_EXPORT_V1 :: {new Date().toISOString()}
            </div>
        </div>
    );
}
