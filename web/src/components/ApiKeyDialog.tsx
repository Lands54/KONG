import React from 'react';

interface ApiKeyDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (apiKey: string) => void;
  title?: string;
  message?: string;
}

export default function ApiKeyDialog({
  open,
  onClose,
  onConfirm,
  title = "AUTH_REQUIRED",
  message = "Session requires API key provision for execution restart."
}: ApiKeyDialogProps) {
  const [apiKey, setApiKey] = React.useState('');
  const [error, setError] = React.useState('');

  if (!open) return null;

  const handleConfirm = () => {
    if (!apiKey.trim()) {
      setError('INPUT_REQUIRED: API_KEY_MISSING');
      return;
    }
    onConfirm(apiKey.trim());
    setApiKey('');
    setError('');
  };

  const handleCancel = () => {
    setApiKey('');
    setError('');
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.4)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000
    }}
      onClick={handleCancel}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '32px',
          width: '90%',
          maxWidth: '450px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 20px 50px rgba(0,0,0,0.2)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{
          fontSize: '11px',
          fontWeight: 800,
          color: '#ef4444',
          letterSpacing: '0.1em',
          marginBottom: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <div style={{ width: '6px', height: '6px', backgroundColor: '#ef4444', borderRadius: '50%' }} />
          {title.toUpperCase()}
        </div>

        <h2 style={{
          margin: '0 0 16px 0',
          fontSize: '20px',
          fontWeight: 800,
          color: '#1e293b'
        }}>
          System Access Prompt
        </h2>

        <p style={{
          margin: '0 0 24px 0',
          fontSize: '13px',
          color: '#64748b',
          lineHeight: 1.5
        }}>
          {message}
        </p>

        <div style={{ marginBottom: '32px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '11px',
            fontWeight: 700,
            color: '#94a3b8',
            letterSpacing: '0.05em'
          }}>
            PROVISIONING_KEY_STR
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value);
              setError('');
            }}
            placeholder="sk-or-v1-..."
            style={{
              width: '100%',
              padding: '12px',
              border: error ? '1px solid #ef4444' : '1px solid #e2e8f0',
              borderRadius: '6px',
              fontSize: '14px',
              fontFamily: 'monospace',
              outline: 'none',
              backgroundColor: '#f8fafc',
              transition: 'all 0.2s',
              boxSizing: 'border-box'
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleConfirm();
              if (e.key === 'Escape') handleCancel();
            }}
            autoFocus
          />
          {error && (
            <p style={{
              margin: '8px 0 0 0',
              fontSize: '11px',
              color: '#ef4444',
              fontWeight: 700
            }}>
              {error}
            </p>
          )}
          <p style={{
            margin: '12px 0 0 0',
            fontSize: '11px',
            color: '#94a3b8'
          }}>
            DOCS: <a
              href="https://openrouter.ai/keys"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#3b82f6', textDecoration: 'none', borderBottom: '1px solid #3b82f6' }}
            >
              openrouter.ai/keys
            </a>
          </p>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '12px'
        }}>
          <button
            onClick={handleCancel}
            style={{
              padding: '10px 20px',
              backgroundColor: 'transparent',
              color: '#64748b',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase'
            }}
          >
            ABORT
          </button>
          <button
            onClick={handleConfirm}
            style={{
              padding: '10px 24px',
              backgroundColor: '#1e293b',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            CONFIRM_PROVISION
          </button>
        </div>
      </div>
    </div>
  );
}
