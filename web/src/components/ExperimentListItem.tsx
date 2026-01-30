import React from 'react';
import { Link } from 'react-router-dom';

interface ExperimentListItemProps {
  experiment: any;
  onRerun: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}

export default function ExperimentListItem({ experiment, onRerun, onDelete }: ExperimentListItemProps) {
  const [isHovered, setIsHovered] = React.useState(false);

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return { color: '#10b981', bg: '#ecfdf5', label: '已完成', icon: '✅' };
      case 'running':
        return { color: '#f59e0b', bg: '#fff9eb', label: '运行中', icon: '⏳' };
      default:
        return { color: '#ef4444', bg: '#fef2f2', label: '失败', icon: '❌' };
    }
  };

  const status = getStatusConfig(experiment.status);

  return (
    <div
      style={{
        marginBottom: '12px'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '16px 24px',
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e2e8f0',
        boxShadow: isHovered ? '0 10px 20px -5px rgba(0, 0, 0, 0.1)' : '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        transition: 'all 0.2s',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* 指示物 */}
        <div style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '3px',
          backgroundColor: status.color
        }} />

        <Link
          to={`/experiments/${experiment.id}`}
          style={{
            flex: 1,
            textDecoration: 'none',
            color: 'inherit',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <strong style={{
              fontSize: '15px',
              color: '#1e293b',
              fontWeight: 800,
              letterSpacing: '-0.01em'
            }}>
              {experiment.name}
            </strong>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: status.bg,
              color: status.color,
              fontSize: '10px',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              {experiment.status}
            </div>
          </div>

          <p style={{
            color: '#64748b',
            fontSize: '13px',
            margin: 0,
            lineHeight: 1.4,
            maxWidth: '90%'
          }}>
            {experiment.goal}
          </p>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            fontSize: '11px',
            color: '#94a3b8',
            marginTop: '4px'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ opacity: 0.6 }}>STRATEGY:</span>
              <span style={{ color: '#64748b', fontWeight: 600 }}>{experiment.haltingStrategy}</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ opacity: 0.6 }}>TS:</span>
              <span style={{ color: '#64748b' }}>
                {new Date(experiment.createdAt).toISOString().replace('T', ' ').substring(0, 19)}
              </span>
            </span>
          </div>
        </Link>

        <div style={{
          display: 'flex',
          gap: '8px',
          opacity: isHovered ? 1 : 0,
          transition: 'all 0.2s',
          marginLeft: '20px'
        }}>
          {(experiment.status === 'completed' || experiment.status === 'failed') && (
            <button
              onClick={(e) => { e.preventDefault(); onRerun(); }}
              style={{
                padding: '6px 12px',
                backgroundColor: '#ffffff',
                color: '#475569',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: 700,
                textTransform: 'uppercase',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f8fafc';
                e.currentTarget.style.borderColor = '#cbd5e1';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#ffffff';
                e.currentTarget.style.borderColor = '#e2e8f0';
              }}
            >
              RERUN
            </button>
          )}
          <button
            onClick={(e) => { e.preventDefault(); onDelete(); }}
            style={{
              padding: '6px 12px',
              backgroundColor: '#ffffff',
              color: '#ef4444',
              border: '1px solid #fee2e2',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '11px',
              fontWeight: 700,
              textTransform: 'uppercase',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#fef2f2';
              e.currentTarget.style.borderColor = '#fca5a5';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#ffffff';
              e.currentTarget.style.borderColor = '#fee2e2';
            }}
          >
            DELETE
          </button>
        </div>
      </div>
    </div>
  );
}
