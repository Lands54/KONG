import React from 'react';

interface GraphSelectorProps {
  selectedGraph: string;
  onSelect: (graph: string) => void;
  availableKeys: string[];
}

export default function GraphSelector({ selectedGraph, onSelect, availableKeys }: GraphSelectorProps) {
  const META: Record<string, { label: string; desc: string }> = {
    'G_B': { label: 'BOTTOM-UP', desc: 'REBEL Extraction Results' },
    'G_T': { label: 'TOP-DOWN', desc: 'GPT Decomposition Results' },
    'G_F': { label: 'FUSED', desc: 'Merged Knowledge Map' },
    'Final': { label: 'FINAL_OUTPUT', desc: 'Complete Discovered Graph' }
  };

  const sortedKeys = React.useMemo(() => {
    return [...availableKeys].sort((a, b) => {
      if (a === 'Final') return 1;
      if (b === 'Final') return -1;
      const aKnown = META.hasOwnProperty(a);
      const bKnown = META.hasOwnProperty(b);
      if (aKnown && !bKnown) return -1;
      if (!aKnown && bKnown) return 1;
      if (a.startsWith('iteration_') && b.startsWith('iteration_')) {
        const numA = parseInt(a.match(/\d+/)?.[0] || '0');
        const numB = parseInt(b.match(/\d+/)?.[0] || '0');
        return numA - numB;
      }
      return a.localeCompare(b);
    });
  }, [availableKeys]);

  if (availableKeys.length === 0) return null;

  return (
    <div style={{
      display: 'flex',
      gap: '2px',
      padding: '4px 24px',
      backgroundColor: '#f1f5f9',
      borderBottom: '1px solid #e2e8f0',
      overflowX: 'auto',
      whiteSpace: 'nowrap'
    }}>
      {sortedKeys.map(key => {
        const meta = META[key] || { label: key.toUpperCase(), desc: key };
        const isSelected = selectedGraph === key;

        return (
          <button
            key={key}
            onClick={() => onSelect(key)}
            style={{
              padding: '6px 16px',
              border: 'none',
              borderRadius: '4px 4px 0 0',
              backgroundColor: isSelected ? '#ffffff' : 'transparent',
              cursor: 'pointer',
              color: isSelected ? '#1e293b' : '#94a3b8',
              fontSize: '11px',
              fontWeight: 800,
              letterSpacing: '0.05em',
              transition: 'all 0.15s',
              flexShrink: 0,
              position: 'relative'
            }}
            title={meta.desc}
          >
            {meta.label}
            {isSelected && (
              <div style={{
                position: 'absolute',
                bottom: '-4px',
                left: 0,
                right: 0,
                height: '4px',
                backgroundColor: '#ffffff'
              }} />
            )}
          </button>
        );
      })}
    </div>
  );
}
