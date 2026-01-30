import React from 'react';
import { ComponentSpec, SlotRequirement } from '../types/components';

interface SlotConfiguratorProps {
    slots: SlotRequirement;
    availableComponents: Record<string, ComponentSpec[]>;  // keyed by category
    values: Record<string, string>;  // slot name -> selected component id
    onChange: (slotName: string, componentId: string) => void;
    disabled?: boolean;
}

export default function SlotConfigurator({
    slots,
    availableComponents,
    values,
    onChange,
    disabled = false
}: SlotConfiguratorProps) {
    const interfaceToCategory = (interfaceType: string): string => {
        if (interfaceType === 'AbstractHaltingStrategy' || interfaceType === 'IHalting') return 'haltings';
        if (interfaceType.startsWith('I')) {
            const name = interfaceType.slice(1).toLowerCase();
            return name.endsWith('s') ? name : name + 's';
        }
        return 'unknown';
    };

    return (
        <div style={{
            padding: '20px',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            backgroundColor: '#ffffff'
        }}>
            {Object.entries(slots).map(([slotName, interfaceType]) => {
                const category = interfaceToCategory(interfaceType);
                const components = availableComponents[category] || [];
                const selectedValue = values[slotName] || '';
                const selectedComp = components.find(c => c.id === selectedValue);

                return (
                    <div key={slotName} style={{ marginBottom: '20px' }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'baseline',
                            marginBottom: '6px'
                        }}>
                            <label style={{
                                fontSize: '11px',
                                fontWeight: 700,
                                color: '#475569',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em'
                            }}>
                                SLOT::{slotName}
                            </label>
                            <span style={{ fontSize: '10px', color: '#94a3b8', fontFamily: 'monospace' }}>
                                interface: {interfaceType}
                            </span>
                        </div>

                        <select
                            value={selectedValue}
                            onChange={(e) => onChange(slotName, e.target.value)}
                            disabled={disabled || components.length === 0}
                            style={{
                                width: '100%',
                                padding: '8px 10px',
                                border: '1px solid #e2e8f0',
                                borderRadius: '6px',
                                fontSize: '13px',
                                fontWeight: 600,
                                backgroundColor: disabled ? '#f8fafc' : (components.length === 0 ? '#fef2f2' : 'white'),
                                color: '#1e293b',
                                cursor: disabled ? 'not-allowed' : 'pointer'
                            }}
                        >
                            <option value="">-- SELECT_{slotName.toUpperCase()} --</option>
                            {components.map(component => (
                                <option key={component.id} value={component.id}>
                                    {component.id.toUpperCase()}
                                </option>
                            ))}
                        </select>

                        {components.length === 0 && (
                            <div style={{
                                marginTop: '4px',
                                fontSize: '10px',
                                color: '#ef4444',
                                fontWeight: 700
                            }}>
                                ERROR: NO_COMPONENTS_FOR_CATEGORY::{category.toUpperCase()}
                            </div>
                        )}

                        {selectedComp && (
                            <div style={{
                                marginTop: '6px',
                                fontSize: '11px',
                                color: '#64748b',
                                padding: '6px 10px',
                                backgroundColor: '#f8fafc',
                                borderLeft: '2px solid #e2e8f0'
                            }}>
                                {selectedComp.description || 'NODE_DESCRIPTION_EMPTY'}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
