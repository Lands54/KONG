import React from 'react';
import { OrchestratorSpec } from '../types/components';
import ParameterConfigPanel from './ParameterConfigPanel';

interface OrchestratorSelectorProps {
    orchestrators: OrchestratorSpec[];
    value: string;
    params: Record<string, any>;
    onChange: (orchestratorId: string) => void;
    onParamChange: (params: Record<string, any>) => void;
    disabled?: boolean;
}

export default function OrchestratorSelector({
    orchestrators,
    value,
    params,
    onChange,
    onParamChange,
    disabled = false
}: OrchestratorSelectorProps) {
    const selected = orchestrators.find(o => o.id === value);
    const [showConfig, setShowConfig] = React.useState(false);
    const isConfigurable = selected && selected.params && Object.keys(selected.params).length > 0;

    return (
        <div style={{ marginBottom: '24px' }}>
            <label style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 600,
                fontSize: '12px',
                color: '#64748b'
            }}>
                CORE_ORCHESTRATOR_MODULE
            </label>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: 700,
                    backgroundColor: disabled ? '#f8fafc' : 'white',
                    color: '#1e293b',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    appearance: 'none',
                    backgroundImage: 'url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2210%22%20height%3D%226%22%20viewBox%3D%220%200%2010%206%22%20fill%3D%22none%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cpath%20d%3D%22M1%201L5%205L9%201%22%20stroke%3D%22%2364748B%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22/%3E%3C/svg%3E")',
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 12px center'
                }}
            >
                <option value="">SELECT_ORCHESTRATOR...</option>
                {orchestrators.map(orchestrator => (
                    <option key={orchestrator.id} value={orchestrator.id}>
                        {orchestrator.id.toUpperCase()}
                    </option>
                ))}
            </select>

            {isConfigurable && (
                <button
                    type="button"
                    onClick={() => setShowConfig(true)}
                    style={{
                        marginTop: '12px',
                        width: '100%',
                        padding: '8px',
                        backgroundColor: '#f1f5f9',
                        color: '#475569',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                    }}
                >
                    <span>⚙️</span> CONFIGURE_CORE_PARAMETERS
                </button>
            )}

            {showConfig && selected && (
                <ParameterConfigPanel
                    spec={selected}
                    values={params}
                    onChange={(k, v) => onParamChange({ ...params, [k]: v })}
                    onClose={() => setShowConfig(false)}
                />
            )}

            {selected && (
                <div style={{
                    marginTop: '12px',
                    padding: '12px',
                    backgroundColor: '#f8fafc',
                    borderLeft: '2px solid #3b82f6',
                    fontSize: '12px',
                    lineHeight: 1.5,
                    color: '#475569'
                }}>
                    <div style={{ fontWeight: 800, fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}>SPECIFICATION_DOC</div>
                    {selected.description || 'NO_SPEC_PROVIDED'}
                </div>
            )}
        </div>
    );
}
