import React from 'react';
import DatasetBrowser from './DatasetBrowser';
import OrchestratorSelector from './OrchestratorSelector';
import ParameterConfigPanel from './ParameterConfigPanel';
import GameStyleSelector from './GameStyleSelector';
import { api } from '../services/apiClient';
import { OrchestratorSpec, ComponentSpec } from '../types/components';

interface CreateExperimentFormProps {
  onSuccess: () => void;
  onCancel?: () => void;
}

/**
 * 实验配置控制台
 * 采用工业控制面板风格：紧凑、等宽字体、明确的功能分区
 */
export default function CreateExperimentForm({ onSuccess, onCancel }: CreateExperimentFormProps) {
  const [formData, setFormData] = React.useState({
    name: '',
    goal: '',
    text: '',
    orchestrator: 'dynamic_halting',
    components: {} as Record<string, string>,
    componentParams: {} as Record<string, Record<string, any>>, // { slotName: { paramName: val } }
    orchestratorParams: {} as Record<string, any>,
    apiKey: '',
    datasetRef: null as null | { datasetId: string; split: string; index: number }
  });

  const [orchestrators, setOrchestrators] = React.useState<OrchestratorSpec[]>([]);
  const [availableComponents, setAvailableComponents] = React.useState<Record<string, ComponentSpec[]>>({});
  const [loading, setLoading] = React.useState(false);
  const [dataLoading, setDataLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showDatasetBrowser, setShowDatasetBrowser] = React.useState(false);
  const [apiKeyStatus, setApiKeyStatus] = React.useState<{ set: boolean, message: string } | null>(null);
  const [showApiKeyInput, setShowApiKeyInput] = React.useState(false);
  const [showPresetDialog, setShowPresetDialog] = React.useState(false);
  const [presetName, setPresetName] = React.useState('');
  const [presets, setPresets] = React.useState<string[]>([]);

  // Load presets list on mount
  React.useEffect(() => {
    const loadPresets = () => {
      const keys = Object.keys(localStorage).filter(k => k.startsWith('prism_preset_'));
      setPresets(keys.map(k => k.replace('prism_preset_', '')));
    };
    loadPresets();
  }, []);

  const handleSavePreset = () => {
    if (!presetName.trim()) return;
    const presetData = {
      orchestrator: formData.orchestrator,
      components: formData.components,
      componentParams: formData.componentParams,
      orchestratorParams: formData.orchestratorParams
    };
    localStorage.setItem(`prism_preset_${presetName}`, JSON.stringify(presetData));
    setPresets(prev => [...new Set([...prev, presetName])]);
    setPresetName('');
    setShowPresetDialog(false);
  };

  const handleLoadPreset = (name: string) => {
    try {
      const raw = localStorage.getItem(`prism_preset_${name}`);
      if (!raw) return;
      const data = JSON.parse(raw);
      setFormData(prev => ({
        ...prev,
        orchestrator: data.orchestrator || prev.orchestrator,
        components: data.components || {},
        componentParams: data.componentParams || {},
        orchestratorParams: data.orchestratorParams || {}
      }));
      setShowPresetDialog(false);
    } catch (e) {
      console.error('Failed to load preset', e);
    }
  };

  const handleDeletePreset = (name: string) => {
    localStorage.removeItem(`prism_preset_${name}`);
    setPresets(prev => prev.filter(p => p !== name));
  };

  // 加载组件目录
  React.useEffect(() => {
    const loadComponentCatalog = async () => {
      try {
        setDataLoading(true);
        const registryResp = await api.components.fetchCatalog() as any;

        if (registryResp.success && registryResp.catalog) {
          const catalog = registryResp.catalog;
          setOrchestrators(catalog.orchestrators || []);
          const components: Record<string, ComponentSpec[]> = {};
          Object.entries(catalog).forEach(([category, list]) => {
            if (category !== 'orchestrators') {
              components[category] = list as ComponentSpec[];
            }
          });
          setAvailableComponents(components);
        }
        setDataLoading(false);
      } catch (err: any) {
        console.error('Failed to load component catalog:', err);
        setError('SYSTEM_CATALOG_UNAVAILABLE');
        setDataLoading(false);
      }
    };
    loadComponentCatalog();
  }, []);

  // 检查 API Key 状态
  React.useEffect(() => {
    api.config.check()
      .then((data: any) => {
        const isKeySet = data.api_key && data.api_key !== "not set";
        setApiKeyStatus({
          set: isKeySet,
          message: isKeySet ? "SYSTEM_AUTHENTICATION_VERIFIED" : "CREDENTIALS_REQUIRED"
        });
      })
      .catch(err => {
        console.error('Error checking API key status:', err);
      });
  }, []);

  // 当编排器变化时，重置组件选择
  React.useEffect(() => {
    if (formData.orchestrator) {
      const selectedOrchestrator = orchestrators.find(o => o.id === formData.orchestrator);
      if (!selectedOrchestrator) return;
      const initialSlots: Record<string, string> = {};
      Object.keys(selectedOrchestrator.slots).forEach(slotName => {
        initialSlots[slotName] = '';
      });

      // Initialize orchestrator params from spec defaults
      const initialParams: Record<string, any> = {};
      if (selectedOrchestrator.params) {
        Object.entries(selectedOrchestrator.params).forEach(([k, p]: [string, any]) => {
          initialParams[k] = p.default;
        });
      }

      setFormData(prev => ({
        ...prev,
        components: initialSlots,
        orchestratorParams: initialParams
      }));
    }
  }, [formData.orchestrator, orchestrators]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const selectedOrchestrator = orchestrators.find(o => o.id === formData.orchestrator);
      if (selectedOrchestrator?.slots) {
        const missingSlots = Object.keys(selectedOrchestrator.slots).filter(
          slotName => !formData.components[slotName]
        );
        if (missingSlots.length > 0) {
          throw new Error(`MISSING_COMPONENT_SLOTS: ${missingSlots.join(', ')}`);
        }
      }

      const requestData: any = {
        name: formData.name,
        goal: formData.goal,
        text: formData.text,
        orchestrator: formData.orchestrator,
        components: formData.components,
        component_params: formData.componentParams,
        params: formData.orchestratorParams
      };

      if (formData.apiKey) {
        requestData.apiKey = formData.apiKey;
      }
      if (formData.datasetRef) {
        requestData.datasetRef = formData.datasetRef;
      }

      const result = await api.experiments.create(requestData);
      onSuccess();
      if (result.id) {
        window.location.href = `/experiments/${result.id}`;
      }
    } catch (err: any) {
      setError(err.message || 'RUNTIME_ERROR: CREATE_SESSION_FAILED');
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  if (dataLoading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
        <span className="animate-pulse">LOADING_CATALOG...</span>
      </div>
    );
  }

  const selectedOrchestrator = orchestrators.find(o => o.id === formData.orchestrator);

  const SectionTitle = ({ children }: { children: string }) => (
    <h3 style={{
      fontSize: '11px',
      fontWeight: 800,
      color: '#94a3b8',
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      marginBottom: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    }}>
      <div style={{ width: '4px', height: '4px', backgroundColor: '#cbd5e1' }} />
      {children}
    </h3>
  );

  const InputWrapper = ({ label, children }: { label: string, children: React.ReactNode }) => (
    <div style={{ marginBottom: '24px' }}>
      <label style={{
        display: 'block',
        marginBottom: '6px',
        fontSize: '12px',
        fontWeight: 600,
        color: '#64748b'
      }}>
        {label}
      </label>
      {children}
    </div>
  );

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    backgroundColor: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    fontSize: '14px',
    color: '#1e293b',
    transition: 'all 0.2s'
  };

  return (
    <div style={{
      padding: '32px',
      backgroundColor: '#ffffff',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.05)',
      maxWidth: '1000px',
      margin: '0 auto'
    }}>
      <header style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: '20px', marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 800, color: '#1e293b' }}>
            SESSION_INITIALIZER
          </h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
            Configure system parameters and component slots for recursive discovery.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setShowPresetDialog(true)}
            style={{
              padding: '6px 12px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              backgroundColor: 'white',
              color: '#64748b',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            📂 PRESETS
          </button>
        </div>
      </header>

      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fee2e2',
          borderRadius: '6px',
          marginBottom: '24px',
          color: '#ef4444',
          fontSize: '12px',
          fontWeight: 600,
          fontFamily: 'monospace'
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {/* Top Section: Metadata & Auth */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
            <div>
              <SectionTitle>BASE_PARAMETERS</SectionTitle>
              <InputWrapper label="EXPERIMENT_IDENTIFIER">
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  style={inputStyle}
                  placeholder="e.g. DYN_HALT_TEST_01"
                />
              </InputWrapper>

              <InputWrapper label="RESEARCH_GOAL">
                <input
                  type="text"
                  name="goal"
                  value={formData.goal}
                  onChange={handleChange}
                  required
                  style={inputStyle}
                  placeholder="Target objective..."
                />
              </InputWrapper>
            </div>

            <div>
              <SectionTitle>EXECUTION_AUTH</SectionTitle>
              {apiKeyStatus && !apiKeyStatus.set && (
                <div style={{ marginBottom: '24px' }}>
                  <button
                    type="button"
                    onClick={() => setShowApiKeyInput(!showApiKeyInput)}
                    style={{
                      padding: '8px 12px',
                      fontSize: '11px',
                      fontWeight: 700,
                      border: '1px solid #fcd34d',
                      borderRadius: '6px',
                      backgroundColor: '#fffbeb',
                      color: '#92400e',
                      cursor: 'pointer',
                      width: '100%',
                      textAlign: 'left',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                  >
                    <span style={{ fontSize: '14px' }}>⚠️</span>
                    {showApiKeyInput ? 'CANCEL_PROVISIONING' : 'PROVISION_API_KEY'}
                  </button>
                  {showApiKeyInput && (
                    <input
                      type="password"
                      name="apiKey"
                      value={formData.apiKey}
                      onChange={handleChange}
                      style={{ ...inputStyle, marginTop: '12px' }}
                      placeholder="sk-or-v1-..."
                    />
                  )}
                </div>
              )}
              {apiKeyStatus?.set && (
                <div style={{
                  fontSize: '11px',
                  color: '#10b981',
                  backgroundColor: '#ecfdf5',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  display: 'inline-block',
                  fontWeight: 700,
                  marginBottom: '24px'
                }}>
                  ✓ SYSTEM_KEY_READY
                </div>
              )}
            </div>
          </div>

          {/* Full Width: Orchestration */}
          <div>
            <SectionTitle>SYSTEM_CORE</SectionTitle>
            <OrchestratorSelector
              orchestrators={orchestrators}
              value={formData.orchestrator}
              params={formData.orchestratorParams}
              onChange={(orchestratorId) => setFormData(prev => ({ ...prev, orchestrator: orchestratorId }))}
              onParamChange={(params) => setFormData(prev => ({ ...prev, orchestratorParams: params }))}
              disabled={loading}
            />
          </div>

          {/* Full Width: Slots (Game Selector) */}
          {selectedOrchestrator?.slots && (
            <div>
              <SectionTitle>COMPONENT_SLOTS</SectionTitle>
              <GameStyleSelector
                slots={selectedOrchestrator.slots}
                availableComponents={availableComponents}
                values={formData.components}
                paramValues={formData.componentParams}
                onChange={(slotName, componentId) => {
                  setFormData(prev => ({
                    ...prev,
                    components: { ...prev.components, [slotName]: componentId },
                    // Reset params when component changes
                    componentParams: { ...prev.componentParams, [slotName]: {} }
                  }));
                }}
                onParamChange={(slotName, params) => {
                  setFormData(prev => ({
                    ...prev,
                    componentParams: { ...prev.componentParams, [slotName]: params }
                  }));
                }}
                disabled={loading}
              />
            </div>
          )}
        </div>

        {/* Full Width Text Input */}
        <div style={{ marginTop: '32px', paddingTop: '32px', borderTop: '1px solid #f1f5f9' }}>
          <SectionTitle>SOURCE_DATA (INPUT)</SectionTitle>
          <div style={{ position: 'relative' }}>
            <textarea
              name="text"
              value={formData.text}
              onChange={handleChange}
              required
              rows={8}
              style={{
                ...inputStyle,
                fontFamily: 'inherit',
                resize: 'vertical',
                paddingRight: '140px'
              }}
              placeholder="Paste research text or select from dataset..."
            />
            <button
              type="button"
              onClick={() => setShowDatasetBrowser(true)}
              style={{
                position: 'absolute',
                top: '12px',
                right: '12px',
                padding: '6px 12px',
                fontSize: '11px',
                fontWeight: 700,
                border: '1px solid #cbd5e1',
                borderRadius: '4px',
                backgroundColor: '#f8fafc',
                color: '#64748b',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}
            >
              BROWSE_DATASETS
            </button>
          </div>
        </div>

        {/* Action Bar */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '40px' }}>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              style={{
                padding: '10px 24px',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                backgroundColor: 'transparent',
                color: '#64748b',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '12px',
                fontWeight: 700,
                textTransform: 'uppercase'
              }}
            >
              ABORT
            </button>
          )}
          <button
            type="submit"
            disabled={loading || !formData.orchestrator}
            style={{
              padding: '10px 32px',
              border: 'none',
              borderRadius: '6px',
              backgroundColor: loading ? '#94a3b8' : '#1e293b',
              color: 'white',
              cursor: (loading || !formData.orchestrator) ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          >
            {loading ? 'INITIALIZING...' : 'START_EXPLORATION'}
          </button>
        </div>
      </form>

      {showDatasetBrowser && (
        <DatasetBrowser
          onSelect={({ goal, text, datasetRef }) => {
            setFormData(prev => ({
              ...prev,
              goal,
              text,
              datasetRef
            }));
            setShowDatasetBrowser(false);
          }}
          onClose={() => setShowDatasetBrowser(false)}
        />
      )}

      {showPresetDialog && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '12px',
            width: '400px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e2e8f0'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: 800, color: '#334155' }}>CONFIGURATION PRESETS</h3>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '8px' }}>SAVE CURRENT CONFIG</div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="Preset Name (e.g. Baseline-v1)"
                  style={{ flex: 1, padding: '8px', fontSize: '12px', border: '1px solid #cbd5e1', borderRadius: '4px' }}
                />
                <button
                  onClick={handleSavePreset}
                  disabled={!presetName}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: '#1e293b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: presetName ? 'pointer' : 'not-allowed',
                    opacity: presetName ? 1 : 0.5
                  }}
                >
                  SAVE
                </button>
              </div>
            </div>

            <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '8px' }}>LOAD PRESET</div>
            <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #f1f5f9', borderRadius: '4px' }}>
              {presets.length === 0 ? (
                <div style={{ padding: '12px', textAlign: 'center', color: '#cbd5e1', fontSize: '11px', fontStyle: 'italic' }}>No saved presets</div>
              ) : (
                presets.map(p => (
                  <div key={p} style={{
                    padding: '8px 12px',
                    borderBottom: '1px solid #f8fafc',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '12px'
                  }}>
                    <span style={{ fontWeight: 600, color: '#475569' }}>{p}</span>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => handleLoadPreset(p)}
                        style={{ border: 'none', background: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '10px', fontWeight: 700 }}
                      >LOAD</button>
                      <button
                        onClick={() => handleDeletePreset(p)}
                        style={{ border: 'none', background: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '10px', fontWeight: 700 }}
                      >DEL</button>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div style={{ marginTop: '20px', textAlign: 'right' }}>
              <button
                onClick={() => setShowPresetDialog(false)}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#f1f5f9',
                  color: '#64748b',
                  border: '1px solid #e2e8f0',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                CLOSE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
