import React from 'react';
import { api } from '../services/apiClient';

type DatasetSpec = {
  dataset_id: string;
  display_name: string;
  task_type: string;
  source: string;
  hf_name?: string | null;
  hf_config?: string | null;
  description?: string;
};

type SamplePreview = {
  index: number;
  query?: string | null;
  context_preview?: string | null;
  context_length?: number | null;
  label?: any;
};

interface DatasetBrowserProps {
  onSelect: (payload: { goal: string; text: string; datasetRef: { datasetId: string; split: string; index: number } }) => void;
  onClose: () => void;
}

/**
 * 数据集浏览器 (Terminal Explorer 风格)
 */
export default function DatasetBrowser({ onSelect, onClose }: DatasetBrowserProps) {
  const [datasets, setDatasets] = React.useState<DatasetSpec[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = React.useState<string>('');
  const [splits, setSplits] = React.useState<string[]>([]);
  const [selectedSplit, setSelectedSplit] = React.useState<string>('');
  const [splitDatasetId, setSplitDatasetId] = React.useState<string>('');
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [samples, setSamples] = React.useState<SamplePreview[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = React.useState<number | null>(null);
  const [detail, setDetail] = React.useState<any>(null);
  const [loadingDetail, setLoadingDetail] = React.useState(false);

  React.useEffect(() => {
    api.datasets.list()
      .then((data: any) => {
        const list: DatasetSpec[] = data.datasets || [];
        setDatasets(list);
        if (list.length > 0) setSelectedDatasetId(list[0].dataset_id);
      })
      .catch((e: any) => setError(e?.message || 'CATALOG_ERROR: REPOSITORY_FETCH_FAILED'));
  }, []);

  React.useEffect(() => {
    if (!selectedDatasetId) return;
    setSplits([]);
    setSelectedSplit('');
    setSplitDatasetId('');
    setPage(1);
    setSamples([]);
    setDetail(null);
    setSelectedIndex(null);

    api.datasets.splits(selectedDatasetId)
      .then((data: any) => {
        const s: string[] = data.splits || [];
        setSplits(s);
        if (s.length > 0) {
          setSelectedSplit(s[0]);
          setSplitDatasetId(selectedDatasetId);
        }
      })
      .catch((e: any) => setError(e?.message || 'SPLIT_FETCH_FAILED'));
  }, [selectedDatasetId]);

  React.useEffect(() => {
    if (!selectedDatasetId || !selectedSplit || splitDatasetId !== selectedDatasetId) return;
    setLoading(true);
    api.datasets.samples(selectedDatasetId, selectedSplit, page, 20)
      .then((data: any) => {
        setSamples(data.samples || []);
        setTotalPages(data.total_pages || 1);
      })
      .catch((e: any) => {
        setError(e?.message || 'SAMPLE_LOAD_FAILURE (CHECK_REMOTE_CONNECTION)');
        setSamples([]);
      })
      .finally(() => setLoading(false));
  }, [selectedDatasetId, selectedSplit, page, splitDatasetId]);

  const loadDetail = async (idx: number) => {
    setSelectedIndex(idx);
    setLoadingDetail(true);
    try {
      const d = await api.datasets.sample(selectedDatasetId, selectedSplit, idx);
      setDetail(d);
    } catch (e: any) {
      setError('DETAIL_FETCH_FAILED');
    } finally {
      setLoadingDetail(false);
    }
  };

  const canSelect = Boolean(detail?.query && (detail?.context || '').length >= 0);

  const ControlSelect = ({ label, value, options, onChange }: any) => (
    <div style={{ marginBottom: '16px' }}>
      <label style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em', display: 'block', marginBottom: '4px' }}>{label}</label>
      <select
        value={value}
        onChange={onChange}
        style={{
          width: '100%',
          padding: '8px 10px',
          backgroundColor: '#1e293b',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 700,
          cursor: 'pointer'
        }}
      >
        {options.map((opt: any) => (
          <option key={opt.id || opt} value={opt.id || opt}>{opt.label || opt}</option>
        ))}
      </select>
    </div>
  );

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.4)',
      backdropFilter: 'blur(4px)',
      zIndex: 2000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        width: '100%',
        maxWidth: '1280px',
        height: '90vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        border: '1px solid #e2e8f0'
      }}>
        {/* Header */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#f8fafc' }}>
          <div>
            <div style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em' }}>REPOSITORY_BROWSER_V1</div>
            <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#1e293b' }}>Knowledge Dataset Explorer</h2>
          </div>
          <button onClick={onClose} style={{ padding: '8px 20px', backgroundColor: 'transparent', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '12px', fontWeight: 700, color: '#64748b', cursor: 'pointer' }}>ABORT</button>
        </div>

        {error && (
          <div style={{ padding: '10px 24px', backgroundColor: '#fef2f2', borderBottom: '1px solid #fee2e2', color: '#ef4444', fontSize: '11px', fontWeight: 700, fontFamily: 'monospace' }}>
            !! {error}
          </div>
        )}

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Sidebar: Dataset Controls & List */}
          <div style={{ width: '380px', backgroundColor: '#0f172a', display: 'flex', flexDirection: 'column', color: '#cbd5e1' }}>
            <div style={{ padding: '24px', borderBottom: '1px solid #1e293b' }}>
              <ControlSelect
                label="PRIMARY_REPOSITORY"
                value={selectedDatasetId}
                onChange={(e: any) => setSelectedDatasetId(e.target.value)}
                options={datasets.map(d => ({ id: d.dataset_id, label: `${d.display_name} [${d.task_type}]` }))}
              />
              <ControlSelect
                label="DATA_SPLIT"
                value={selectedSplit}
                onChange={(e: any) => { setSelectedSplit(e.target.value); setPage(1); }}
                options={splits}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                <div style={{ fontSize: '10px', fontWeight: 800, color: '#64748b' }}>PAGE {page}/{totalPages}</div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} style={{ padding: '4px 8px', backgroundColor: '#1e293b', border: 'none', borderRadius: '4px', color: '#fff', fontSize: '10px', cursor: 'pointer', opacity: page <= 1 ? 0.5 : 1 }}>PREV</button>
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} style={{ padding: '4px 8px', backgroundColor: '#1e293b', border: 'none', borderRadius: '4px', color: '#fff', fontSize: '10px', cursor: 'pointer', opacity: page >= totalPages ? 0.5 : 1 }}>NEXT</button>
                </div>
              </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
              {loading ? <div style={{ fontSize: '11px', color: '#64748b', textAlign: 'center', padding: '20px' }} className="animate-pulse">BUFFERING_SAMPLES...</div> :
                samples.map(s => (
                  <div
                    key={s.index}
                    onClick={() => loadDetail(s.index)}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '6px',
                      marginBottom: '8px',
                      cursor: 'pointer',
                      backgroundColor: selectedIndex === s.index ? '#1e293b' : 'transparent',
                      border: selectedIndex === s.index ? '1px solid #3b82f6' : '1px solid transparent',
                      transition: 'all 0.15s'
                    }}
                  >
                    <div style={{ fontSize: '10px', color: '#94a3b8', fontFamily: 'monospace', marginBottom: '4px' }}>#{s.index}</div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: selectedIndex === s.index ? '#fff' : '#cbd5e1', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {s.query || '(EMPTY_QUERY)'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {s.context_preview || 'NO_CONTEXT_PREVIEW'}
                    </div>
                  </div>
                ))
              }
            </div>
          </div>

          {/* Main Content: Sample Detail View */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '32px', backgroundColor: '#fff' }}>
            {!detail && !loadingDetail && (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyItems: 'center', flexDirection: 'column', color: '#cbd5e1', paddingTop: '100px' }}>
                <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔭</div>
                <div style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.2em' }}>Select Sample to Inspect</div>
              </div>
            )}
            {loadingDetail && <div style={{ fontSize: '11px', color: '#64748b' }} className="animate-pulse">LOAD_SAMPLE_FULL_DATA::FETCHING...</div>}

            {detail && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em' }}>SAMPLE_METADATA_BLOCK</div>
                    <h1 style={{ margin: '4px 0', fontSize: '24px', fontWeight: 800, color: '#1e293b' }}>
                      PTR_{detail.index}_REF
                    </h1>
                    <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                      <span style={{ fontSize: '10px', fontWeight: 700, backgroundColor: '#f1f5f9', padding: '2px 6px', borderRadius: '4px', color: '#64748b' }}>LABEL::{String(detail.label).toUpperCase()}</span>
                      {detail.metadata?.category && <span style={{ fontSize: '10px', fontWeight: 700, backgroundColor: '#f1f5f9', padding: '2px 6px', borderRadius: '4px', color: '#64748b' }}>CAT::{detail.metadata.category.toUpperCase()}</span>}
                    </div>
                  </div>
                  <button
                    disabled={!canSelect}
                    onClick={() => {
                      onSelect({
                        goal: detail.query || '',
                        text: detail.context || '',
                        datasetRef: { datasetId: selectedDatasetId, split: selectedSplit, index: detail.index },
                      });
                      onClose();
                    }}
                    style={{
                      padding: '12px 24px',
                      backgroundColor: canSelect ? '#1e293b' : '#cbd5e1',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 800,
                      textTransform: 'uppercase',
                      cursor: canSelect ? 'pointer' : 'not-allowed',
                      boxShadow: canSelect ? '0 4px 12px rgba(0,0,0,0.1)' : 'none'
                    }}
                  >
                    START_RESEARCH_SESSION
                  </button>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '8px', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px' }}>RESEARCH_QUERY (GOAL)</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#1e293b', lineHeight: 1.5, padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    {detail.query || "SYSTEM::NULL_VALUE"}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '8px', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px' }}>KNOWLEDGE_CONTEXT (INPUT)</div>
                  <div style={{
                    fontSize: '14px',
                    color: '#475569',
                    lineHeight: 1.6,
                    padding: '16px',
                    backgroundColor: '#fff',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    maxHeight: '400px',
                    overflowY: 'auto',
                    fontFamily: 'inherit'
                  }}>
                    {detail.context || "SYSTEM::CONTEXT_BLANK - Requires retrieval stage or direct input."}
                  </div>
                </div>

                {detail.evidence && (
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: '#94a3b8', marginBottom: '8px', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px' }}>GROUND_TRUTH_EVIDENCE (TRACE)</div>
                    <pre style={{ backgroundColor: '#0f172a', color: '#10b981', padding: '16px', borderRadius: '8px', fontSize: '11px', overflow: 'auto' }}>
                      {JSON.stringify(detail.evidence, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
