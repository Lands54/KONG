import React, { useEffect, useState } from 'react';
import { errorBus, ErrorEvent } from '../utils/errorBus';

export const ErrorToast: React.FC = () => {
    const [error, setError] = useState<ErrorEvent | null>(null);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const unsubscribe = errorBus.subscribe((e) => {
            setError(e);
            setVisible(true);
            // Auto hide after 5 seconds
            setTimeout(() => setVisible(false), 5000);
        });
        return unsubscribe;
    }, []);

    if (!visible || !error) return null;

    return (
        <div style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            maxWidth: '400px',
            backgroundColor: '#fef2f2',
            borderLeft: '4px solid #ef4444',
            borderRadius: '6px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            padding: '16px',
            zIndex: 9999,
            animation: 'slideIn 0.3s ease-out'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                    <div style={{ fontWeight: 700, color: '#991b1b', marginBottom: '4px', fontSize: '14px' }}>
                        {error.code || 'Error'}
                    </div>
                    <div style={{ color: '#b91c1c', fontSize: '13px', lineHeight: '1.5' }}>
                        {error.message}
                    </div>
                </div>
                <button
                    onClick={() => setVisible(false)}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: '#991b1b',
                        cursor: 'pointer',
                        fontSize: '16px',
                        padding: '0 0 0 12px'
                    }}
                >
                    ×
                </button>
            </div>
            <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
        </div>
    );
};
