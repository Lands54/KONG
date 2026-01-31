import React from 'react';
import { useParams, Link } from 'react-router-dom';
import GraphVisualization from '../components/GraphVisualization';
import ExperimentMetrics from '../components/ExperimentMetrics';
import GraphSelector from '../components/GraphSelector';
import IntermediateDataPanel from '../components/IntermediateDataPanel';
import NodeMetadataPanel from '../components/NodeMetadataPanel';
import ApiKeyDialog from '../components/ApiKeyDialog';
import { api } from '../services/apiClient';
import { useWebSocket } from '../hooks/useWebSocket';
import { LiveLogPanel, LogEntry } from '../components/LiveLogPanel';

export default function ExperimentPage() {
  const { id } = useParams<{ id: string }>();
  const [experiment, setExperiment] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [selectedGraph, setSelectedGraph] = React.useState<string>('Final');
  const [selectedNode, setSelectedNode] = React.useState<any>(null);
  const [showApiKeyDialog, setShowApiKeyDialog] = React.useState(false);
  const [logs, setLogs] = React.useState<LogEntry[]>([]);

  // WebSocket 连接
  const { lastEvent } = useWebSocket(id);

  const fetchExperiment = React.useCallback(() => {
    if (!id) return;

    api.experiments.get(id)
      .then((data: any) => {
        setExperiment((prev: any) => ({
          ...data,
          // 保留当前已经收到的遥测数据，以防 API 返回的数据有滞后（虽然理应一致，但防御性编程）
          intermediate_stats: {
            ...data.intermediate_stats,
            ...(prev?.intermediate_stats || {})
          }
        }));
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching experiment:', err);
        setLoading(false);
      });
  }, [id]);

  // 处理 WebSocket 消息 (统一切换到 lastEvent)
  React.useEffect(() => {
    if (!lastEvent) return;

    // 处理状态更新
    if (lastEvent.type === 'status_update' && lastEvent.experimentId === id) {
      setExperiment((prev: any) => {
        if (prev) {
          return { ...prev, status: lastEvent.data };
        }
        return prev;
      });
      if (lastEvent.data !== 'running') {
        fetchExperiment();
      }
    }

    // 处理图更新
    if (lastEvent.type === 'graph_update' && lastEvent.experimentId === id) {
      // 后端仍然会在大阶段结束时发送 generic update，触发拉取
      fetchExperiment();
    }

    // 处理日志 (LOG)
    if (lastEvent.type === 'log' && lastEvent.experimentId === id) {
      // 数据结构与之前保持兼容，或根据 StandardEvent 调整
      // Python 端: payload = { message, level }
      // standard event data = payload
      setLogs(prev => [...prev, lastEvent.data]);
    }

    // 处理实时遥测 (TELEMETRY) - 核心新增
    if (lastEvent.type === 'telemetry' && lastEvent.experimentId === id) {
      const telemetryData = lastEvent.data;

      // 更新中间状态统计
      if (telemetryData.intermediate_stats) {
        setExperiment((prev: any) => {
          if (!prev) return prev;
          return {
            ...prev,
            intermediate_stats: {
              ...(prev.intermediate_stats || {}),
              ...telemetryData.intermediate_stats
            }
          };
        });
      }
    }

  }, [lastEvent, id, fetchExperiment]);

  React.useEffect(() => {
    fetchExperiment();
  }, [id, fetchExperiment]);

  // 如果实验正在运行，每3秒轮询一次（作为 WebSocket 的备用方案）
  React.useEffect(() => {
    if (!experiment || experiment.status !== 'running') {
      return;
    }

    const interval = setInterval(() => {
      fetchExperiment();
    }, 3000);

    return () => clearInterval(interval);
  }, [experiment?.status, fetchExperiment]);

  // 计算可用图键列表 (动态发现)
  const availableKeys = React.useMemo(() => {
    if (!experiment) return [];
    const keys: string[] = [];
    if (experiment.intermediate_graphs) {
      Object.keys(experiment.intermediate_graphs).forEach(key => {
        const g = experiment.intermediate_graphs[key];
        if (g && g.nodes && Object.keys(g.nodes).length > 0) {
          keys.push(key);
        }
      });
    }
    if (experiment.graph && experiment.graph.nodes && Object.keys(experiment.graph.nodes).length > 0) {
      keys.push('Final');
    }
    return keys;
  }, [experiment]);

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
        <span className="animate-pulse">MOUNTING_RESEARCH_ENVIRONMENT...</span>
      </div>
    );
  }

  if (!experiment) {
    return (
      <div style={{ padding: '60px', textAlign: 'center' }}>
        <p style={{ color: '#ef4444', fontWeight: 700 }}>ERROR::SESSION_NOT_FOUND</p>
        <Link to="/" style={{ color: '#3b82f6', fontSize: '12px', textTransform: 'uppercase' }}>Return to List</Link>
      </div>
    );
  }

  const getCurrentGraph = () => {
    if (selectedGraph === 'Final') return experiment.graph;
    return experiment.intermediate_graphs?.[selectedGraph] || experiment.graph;
  };

  const handleRerun = async (apiKey?: string) => {
    if (!window.confirm('确定要重新运行这个实验吗？这将清除当前结果并重新开始。')) return;
    if (experiment?.usedFrontendApiKey && !apiKey) {
      setShowApiKeyDialog(true);
      return;
    }
    try {
      await api.experiments.rerun(id!, apiKey || '');
      window.location.reload();
    } catch (error: any) {
      console.error('Error rerunning experiment:', error);
      if (error.message?.includes('API_KEY_REQUIRED') || error?.error === 'API_KEY_REQUIRED') {
        setShowApiKeyDialog(true);
      } else {
        alert('重新运行失败: ' + (error.message || 'Unknown error'));
      }
    }
  };

  const handleApiKeyConfirm = (apiKey: string) => {
    setShowApiKeyDialog(false);
    handleRerun(apiKey);
  };

  const handleDelete = async () => {
    if (!window.confirm('确定要删除这个实验吗？此操作无法撤销！')) return;
    try {
      await api.experiments.delete(id!);
      window.location.href = '/';
    } catch (error) {
      alert('删除失败');
    }
  };

  const handleStop = async () => {
    if (!window.confirm('确定要停止当前任务吗？')) return;
    try {
      await api.experiments.cancel(id!);
      // 给一点时间让后端处理
      setTimeout(() => fetchExperiment(), 500);
    } catch (error) {
      alert('停止失败');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#f8fafc' }}>
      {/* Precision Navigation Bar */}
      <div style={{
        padding: '12px 24px',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        zIndex: 50
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <Link to="/" style={{
              textDecoration: 'none',
              color: '#94a3b8',
              fontSize: '18px',
              fontWeight: 700,
              padding: '4px 8px',
              borderRadius: '6px',
              backgroundColor: '#f1f5f9'
            }}>←</Link>
            <div>
              <div style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em' }}>EXPERIMENT_SESSION</div>
              <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#1e293b' }}>
                {experiment.name}
              </h1>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '9px', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em' }}>STATUS_CODE</div>
              <div style={{
                fontSize: '12px',
                fontWeight: 700,
                color: (experiment.status === 'completed') ? '#10b981' : ((experiment.status === 'running') ? '#f59e0b' : '#ef4444'),
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                justifyContent: 'flex-end'
              }}>
                {experiment.status === 'running' && <span className="animate-pulse" style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'currentColor' }} />}
                {(experiment.status || 'UNKNOWN').toUpperCase()}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              {experiment.status === 'running' && (
                <button
                  onClick={handleStop}
                  style={{
                    padding: '6px 14px',
                    backgroundColor: '#fffbeb',
                    color: '#b45309',
                    border: '1px solid #fcd34d',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase'
                  }}
                >
                  STOP
                </button>
              )}
              {(experiment.status === 'completed' || experiment.status === 'failed' || experiment.status === 'cancelled') && (
                <button
                  onClick={() => handleRerun()}
                  style={{
                    padding: '6px 14px',
                    backgroundColor: '#ffffff',
                    color: '#475569',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase'
                  }}
                >
                  RERUN
                </button>
              )}
              <button
                onClick={handleDelete}
                style={{
                  padding: '6px 14px',
                  backgroundColor: '#ffffff',
                  color: '#ef4444',
                  border: '1px solid #fee2e2',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '11px',
                  fontWeight: 700,
                  textTransform: 'uppercase'
                }}
              >
                DELETE
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Sub-header: Metadata Info Strip */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '24px',
        padding: '8px 24px',
        backgroundColor: '#f1f5f9',
        borderBottom: '1px solid #e2e8f0',
        fontSize: '11px',
        color: '#64748b'
      }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          <span style={{ fontWeight: 800, color: '#94a3b8' }}>GOAL:</span>
          <span style={{ color: '#475569' }}>{experiment.goal}</span>
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          <span style={{ fontWeight: 800, color: '#94a3b8' }}>STRATEGY:</span>
          <span style={{ color: '#475569', fontWeight: 700 }}>{experiment.haltingStrategy}</span>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px', fontFamily: 'monospace' }}>
          <span style={{ fontWeight: 800, color: '#94a3b8' }}>ID:</span>
          <span>{id}</span>
        </div>
      </div>

      <GraphSelector
        selectedGraph={selectedGraph}
        onSelect={setSelectedGraph}
        availableKeys={availableKeys}
      />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Main Canvas Area */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#fff',
          margin: '12px',
          borderRadius: '8px',
          border: '1px solid #e2e8f0',
          overflow: 'hidden',
          boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)'
        }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <GraphVisualization
              graph={getCurrentGraph()}
              experimentId={id!}
              onNodeClick={(node) => setSelectedNode(node)}
            />
          </div>
          <div style={{ padding: '0 12px 12px 12px' }}>
            {/* Live Debug Terminal */}
            <LiveLogPanel logs={logs} height="200px" />
          </div>
        </div>

        {/* Right Inspection Column */}
        <div style={{
          width: '380px',
          padding: '12px 12px 12px 0',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            padding: '20px',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '11px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              SYSTEM_STATS_TELEMETRY
            </h3>
            <IntermediateDataPanel intermediateStats={experiment.intermediate_stats} />
          </div>

          <div style={{
            backgroundColor: '#ffffff',
            padding: '20px',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '11px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              EVALUATION_METRICS
            </h3>
            <ExperimentMetrics experimentId={id!} data={experiment} />
          </div>
        </div>

        {/* Selected Node Inspector (Floating Overlay) */}
        {selectedNode && (
          <NodeMetadataPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </div>

      <ApiKeyDialog
        open={showApiKeyDialog}
        onClose={() => setShowApiKeyDialog(false)}
        onConfirm={handleApiKeyConfirm}
        title="AUTH_REQUIRED"
        message="Session requires API key provision for execution restart."
      />
    </div>
  );
}
