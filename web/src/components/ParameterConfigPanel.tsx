import React from 'react';
import { ComponentSpec } from '../types/components';

interface ParameterConfigPanelProps {
    spec: ComponentSpec;
    values: Record<string, any>;
    onChange: (key: string, value: any) => void;
    onBatchChange?: (values: Record<string, any>) => void;
    onClose: () => void;
}

export default function ParameterConfigPanel({ spec, values, onChange, onBatchChange, onClose }: ParameterConfigPanelProps) {
    const [showPresets, setShowPresets] = React.useState(false);
    const [presetName, setPresetName] = React.useState('');
    const [savedPresets, setSavedPresets] = React.useState<string[]>([]);

    // Load presets for this specific component type
    React.useEffect(() => {
        const loadPresets = () => {
            const prefix = `kong_comp_preset_${spec.id}_`;
            const keys = Object.keys(localStorage).filter(k => k.startsWith(prefix));
            setSavedPresets(keys.map(k => k.replace(prefix, '')));
        };
        loadPresets();
    }, [spec.id]);

    const handleSavePreset = () => {
        if (!presetName.trim()) return;
        const key = `kong_comp_preset_${spec.id}_${presetName}`;
        localStorage.setItem(key, JSON.stringify(values));
        setSavedPresets(prev => [...new Set([...prev, presetName])]);
        setPresetName('');
    };

    const handleLoadPreset = (name: string) => {
        const key = `kong_comp_preset_${spec.id}_${name}`;
        const raw = localStorage.getItem(key);
        if (raw && onBatchChange) {
            try {
                const loadedValues = JSON.parse(raw);
                onBatchChange(loadedValues);
            } catch (e) {
                console.error("Failed to parse component preset", e);
            }
        }
    };

    const handleDeletePreset = (name: string) => {
        const key = `kong_comp_preset_${spec.id}_${name}`;
        localStorage.removeItem(key);
        setSavedPresets(prev => prev.filter(p => p !== name));
    };

    if (!spec.params) return null;

    const renderInput = (key: string, paramInfo: any) => {
        const value = values[key] ?? paramInfo.default;

        // Boolean -> Toggle
        if (paramInfo.type === 'boolean') {
            return (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <button
                        type="button"
                        onClick={() => onChange(key, !value)}
                        style={{
                            width: '40px',
                            height: '20px',
                            borderRadius: '10px',
                            backgroundColor: value ? '#10b981' : '#cbd5e1',
                            position: 'relative',
                            transition: 'all 0.2s',
                            border: 'none',
                            cursor: 'pointer'
                        }}
                    >
                        <div style={{
                            width: '16px',
                            height: '16px',
                            borderRadius: '50%',
                            backgroundColor: 'white',
                            position: 'absolute',
                            top: '2px',
                            left: value ? '22px' : '2px',
                            transition: 'all 0.2s',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
                        }} />
                    </button>
                    <span style={{ fontSize: '12px', color: '#1e293b', fontWeight: 600 }}>
                        {value ? 'ENABLED' : 'DISABLED'}
                    </span>
                </div>
            );
        }

        // Enum -> Select
        if (paramInfo.enum) {
            return (
                <select
                    value={value}
                    onChange={(e) => onChange(key, e.target.value)}
                    style={{
                        width: '100%',
                        padding: '6px 8px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '4px',
                        fontSize: '12px',
                        backgroundColor: '#f8fafc'
                    }}
                >
                    {paramInfo.enum.map((opt: string) => (
                        <option key={opt} value={opt}>{opt}</option>
                    ))}
                </select>
            );
        }

        // Number -> Slider + Input
        if (paramInfo.type === 'number' || paramInfo.type === 'integer') {
            // Heuristic: If default is between 0 and 1, assuming probability/ratio -> step 0.01
            // If integer, step 1
            const isFloat = paramInfo.type === 'number';
            const step = isFloat ? 0.01 : 1;
            const min = paramInfo.minimum ?? (value > 100 ? 0 : 0); // basic guess
            const max = paramInfo.maximum ?? (value > 100 ? value * 2 : (value > 1 ? 100 : 1));

            return (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                        type="range"
                        min={min}
                        max={max}
                        step={step}
                        value={value}
                        onChange={(e) => onChange(key, isFloat ? parseFloat(e.target.value) : parseInt(e.target.value))}
                        style={{ flex: 1 }}
                    />
                    <input
                        type="number"
                        step={step}
                        value={value}
                        onChange={(e) => onChange(key, isFloat ? parseFloat(e.target.value) : parseInt(e.target.value))}
                        style={{
                            width: '60px',
                            padding: '4px',
                            fontSize: '11px',
                            textAlign: 'right',
                            border: '1px solid #cbd5e1',
                            borderRadius: '4px'
                        }}
                    />
                </div>
            );
        }

        // String / Default
        return (
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(key, e.target.value)}
                style={{
                    width: '100%',
                    padding: '6px 8px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '4px',
                    fontSize: '12px'
                }}
            />
        );
    };

    return (
        <div style={{
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(15, 23, 42, 0.6)', // Darker backdrop
            backdropFilter: 'blur(4px)',
            zIndex: 9999, // High z-index to overlay everything
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '20px'
        }}>
            <div style={{
                width: '90vw',
                maxWidth: '1000px',
                height: '80vh',
                backgroundColor: '#ffffff',
                borderRadius: '16px', // Slightly more rounded
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)', // Deeper shadow
                display: 'flex',
                flexDirection: 'column',
                padding: '32px',
                border: '1px solid #e2e8f0',
                animation: 'slideIn 0.2s ease-out'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ fontSize: '16px' }}>⚙️</div>
                        <div>
                            <h4 style={{ margin: 0, fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: '#475569' }}>
                                CONFIG :: {spec.id}
                            </h4>
                            <span style={{ fontSize: '10px', color: '#94a3b8' }}>PARAMETER_TUNING_MODULE</span>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <button
                            onClick={() => setShowPresets(!showPresets)}
                            style={{
                                border: '1px solid #e2e8f0',
                                background: showPresets ? '#f1f5f9' : 'white',
                                borderRadius: '4px',
                                padding: '4px 8px',
                                fontSize: '10px',
                                fontWeight: 700,
                                cursor: 'pointer',
                                color: '#64748b'
                            }}
                        >
                            {showPresets ? 'HIDE_PRESETS' : 'MANAGE_PRESETS'}
                        </button>
                        <button
                            onClick={onClose}
                            style={{
                                border: 'none',
                                background: 'none',
                                fontSize: '18px',
                                cursor: 'pointer',
                                color: '#64748b'
                            }}
                        >
                            ×
                        </button>
                    </div>
                </div>

                {showPresets && (
                    <div style={{
                        marginBottom: '20px',
                        padding: '16px',
                        backgroundColor: '#f8fafc',
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        fontSize: '12px'
                    }}>
                        <div style={{ marginBottom: '12px', display: 'flex', gap: '8px' }}>
                            <input
                                type="text"
                                value={presetName}
                                onChange={(e) => setPresetName(e.target.value)}
                                placeholder="New Preset Name..."
                                style={{
                                    flex: 1,
                                    padding: '6px',
                                    borderRadius: '4px',
                                    border: '1px solid #cbd5e1',
                                    fontSize: '11px'
                                }}
                            />
                            <button
                                onClick={handleSavePreset}
                                disabled={!presetName}
                                style={{
                                    padding: '6px 12px',
                                    backgroundColor: '#3b82f6',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '10px',
                                    fontWeight: 700,
                                    cursor: presetName ? 'pointer' : 'not-allowed',
                                    opacity: presetName ? 1 : 0.6
                                }}
                            >
                                SAVE_CONFIG
                            </button>
                        </div>

                        <div>
                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', marginBottom: '8px' }}>SAVED_PRESETS</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                {savedPresets.length === 0 && <span style={{ color: '#cbd5e1', fontStyle: 'italic', fontSize: '10px' }}>No saved presets</span>}
                                {savedPresets.map(p => (
                                    <div key={p} style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        padding: '4px 8px',
                                        backgroundColor: 'white',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '4px'
                                    }}>
                                        <span style={{ fontWeight: 600, color: '#475569', fontSize: '11px' }}>{p}</span>
                                        <button
                                            onClick={() => handleLoadPreset(p)}
                                            style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: '10px', color: '#2563eb', fontWeight: 700, padding: 0 }}
                                            title="Load"
                                        >
                                            LOAD
                                        </button>
                                        <button
                                            onClick={() => handleDeletePreset(p)}
                                            style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: '10px', color: '#ef4444', fontWeight: 700, padding: 0 }}
                                            title="Delete"
                                        >
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', // 2-3 columns depending on screen
                    gap: '20px',
                    alignContent: 'start',
                    paddingRight: '8px',
                    marginTop: '16px'
                }}>
                    {Object.entries(spec.params).map(([key, info]: [string, any]) => (
                        <div key={key} style={{
                            padding: '16px',
                            backgroundColor: '#f8fafc',
                            borderRadius: '8px',
                            border: '1px solid #e2e8f0',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <label style={{ fontSize: '11px', fontWeight: 700, color: '#334155' }}>
                                    {key.toUpperCase()}
                                </label>
                                <span style={{ fontSize: '9px', color: '#94a3b8', fontStyle: 'italic' }}>
                                    {info.type}
                                </span>
                            </div>
                            <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '6px' }}>
                                {info.description}
                            </div>
                            {renderInput(key, info)}
                        </div>
                    ))}
                </div>

                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #f1f5f9', textAlign: 'right' }}>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '6px 16px',
                            backgroundColor: '#1e293b',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 700,
                            cursor: 'pointer'
                        }}
                    >
                        APPLY_CHANGES
                    </button>
                </div>
            </div>
        </div>
    );
}
