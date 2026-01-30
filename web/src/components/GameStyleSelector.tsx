import React from 'react';
import { ComponentSpec, SlotRequirement } from '../types/components';
import ParameterConfigPanel from './ParameterConfigPanel';

interface GameStyleSelectorProps {
    slots: SlotRequirement;
    availableComponents: Record<string, ComponentSpec[]>;
    values: Record<string, string>; // selected component IDs
    paramValues: Record<string, Record<string, any>>; // { slotName: { paramName: val } }
    onChange: (slotName: string, componentId: string) => void;
    onParamChange: (slotName: string, params: Record<string, any>) => void;
    disabled?: boolean;
}

export default function GameStyleSelector({
    slots,
    availableComponents,
    values,
    paramValues,
    onChange,
    onParamChange,
    disabled = false
}: GameStyleSelectorProps) {

    // Track which slot is currently being configured (for the popover panel)
    const [configuringSlot, setConfiguringSlot] = React.useState<string | null>(null);

    const interfaceToCategory = (interfaceType: string): string => {
        if (interfaceType === 'AbstractHaltingStrategy' || interfaceType === 'IHalting') return 'haltings';
        if (interfaceType.startsWith('I')) {
            const name = interfaceType.slice(1).toLowerCase();
            return name.endsWith('s') ? name : name + 's';
        }
        return 'unknown';
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            {Object.entries(slots).map(([slotName, interfaceType]) => {
                const category = interfaceToCategory(interfaceType);
                const components = availableComponents[category] || [];
                const selectedId = values[slotName];
                const selectedComponent = components.find(c => c.id === selectedId);

                return (
                    <div key={slotName} style={{ position: 'relative' }}>
                        {/* Slot Header */}
                        <div style={{
                            display: 'flex',
                            alignItems: 'baseline',
                            gap: '8px',
                            marginBottom: '12px',
                            borderBottom: '1px solid #e2e8f0',
                            paddingBottom: '8px'
                        }}>
                            <h4 style={{
                                margin: 0,
                                fontSize: '13px',
                                fontWeight: 800,
                                color: '#334155',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em'
                            }}>
                                SLOT :: {slotName}
                            </h4>
                            <span style={{
                                fontSize: '10px',
                                color: '#94a3b8',
                                fontFamily: 'monospace',
                                textTransform: 'uppercase'
                            }}>
                                [{interfaceType}]
                            </span>
                        </div>

                        {/* Component Grid */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                            gap: '12px'
                        }}>
                            {components.map(comp => {
                                const isSelected = comp.id === selectedId;
                                const isConfigurable = comp.id === selectedId && comp.params && Object.keys(comp.params).length > 0;

                                return (
                                    <div
                                        key={comp.id}
                                        onClick={() => !disabled && onChange(slotName, comp.id)}
                                        style={{
                                            position: 'relative',
                                            padding: '12px',
                                            border: isSelected ? '1px solid #3b82f6' : '1px solid #e2e8f0',
                                            borderRadius: '8px',
                                            backgroundColor: isSelected ? '#eff6ff' : 'white',
                                            cursor: disabled ? 'not-allowed' : 'pointer',
                                            transition: 'all 0.2s',
                                            boxShadow: isSelected ? '0 4px 12px -2px rgba(59, 130, 246, 0.15)' : 'none',
                                            opacity: disabled ? 0.6 : 1
                                        }}
                                        onMouseEnter={(e) => {
                                            if (!isSelected && !disabled) {
                                                e.currentTarget.style.borderColor = '#cbd5e1';
                                                e.currentTarget.style.backgroundColor = '#f8fafc';
                                            }
                                        }}
                                        onMouseLeave={(e) => {
                                            if (!isSelected) {
                                                e.currentTarget.style.borderColor = '#e2e8f0';
                                                e.currentTarget.style.backgroundColor = 'white';
                                            }
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                                            <div style={{
                                                fontSize: '12px',
                                                fontWeight: 700,
                                                color: isSelected ? '#1e40af' : '#475569',
                                                textTransform: 'uppercase'
                                            }}>
                                                {comp.name || comp.id}
                                            </div>
                                            {isSelected && (
                                                <div style={{ fontSize: '10px', color: '#3b82f6', fontWeight: 800 }}>✓</div>
                                            )}
                                        </div>

                                        <p style={{
                                            margin: 0,
                                            fontSize: '10px',
                                            color: '#64748b',
                                            lineHeight: '1.4',
                                            height: '40px',
                                            overflow: 'hidden',
                                            display: '-webkit-box',
                                            WebkitLineClamp: 3,
                                            WebkitBoxOrient: 'vertical'
                                        }}>
                                            {comp.description || 'No description available.'}
                                        </p>

                                        {/* Config Button (Only if selected + has params) */}
                                        {isConfigurable && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setConfiguringSlot(slotName);
                                                }}
                                                style={{
                                                    marginTop: '12px',
                                                    width: '100%',
                                                    padding: '6px',
                                                    backgroundColor: '#dbeafe',
                                                    color: '#1e40af',
                                                    border: '1px solid #bfdbfe',
                                                    borderRadius: '4px',
                                                    fontSize: '10px',
                                                    fontWeight: 700,
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    gap: '4px'
                                                }}
                                            >
                                                <span>⚙️</span> CONFIGURE
                                            </button>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Parameter Config Panel Overlay */}
                        {configuringSlot === slotName && selectedComponent && (
                            <ParameterConfigPanel
                                spec={selectedComponent}
                                values={paramValues[slotName] || {}}
                                onChange={(key, val) => {
                                    // Deep Merge update
                                    const currentSlotParams = paramValues[slotName] || {};
                                    onParamChange(slotName, { ...currentSlotParams, [key]: val });
                                }}
                                onBatchChange={(newValues) => {
                                    onParamChange(slotName, newValues);
                                }}
                                onClose={() => setConfiguringSlot(null)}
                            />
                        )}

                        {components.length === 0 && (
                            <div style={{ fontSize: '11px', color: '#ef4444', fontStyle: 'italic', marginTop: '8px' }}>
                                NO_COMPONENTS_FOUND_FOR_CATEGORY::{category.toUpperCase()}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
