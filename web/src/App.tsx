import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import ExperimentPage from './pages/ExperimentPage';
import CreateExperimentForm from './components/CreateExperimentForm';
import ExperimentListItem from './components/ExperimentListItem';
import ApiKeyDialog from './components/ApiKeyDialog';
import { api } from './services/apiClient';

function ExperimentList() {
  const [experiments, setExperiments] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const [showApiKeyDialog, setShowApiKeyDialog] = React.useState(false);
  const [rerunExperimentId, setRerunExperimentId] = React.useState<string | null>(null);

  const fetchExperiments = () => {
    setLoading(true);
    api.experiments.list()
      .then((data: any) => {
        setExperiments(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching experiments:', err);
        setLoading(false);
      });
  };

  React.useEffect(() => {
    fetchExperiments();
  }, []);

  // 如果有运行中的实验，每3秒轮询一次
  React.useEffect(() => {
    const hasRunning = experiments.some(exp => exp.status === 'running');
    if (!hasRunning) return;

    const interval = setInterval(() => {
      fetchExperiments();
    }, 3000);

    return () => clearInterval(interval);
  }, [experiments]);

  const handleCreateSuccess = () => {
    setShowCreateForm(false);
    // 刷新实验列表
    fetchExperiments();
  };

  const handleRerun = async (id: string, apiKey?: string) => {
    if (!window.confirm('确定要重新运行这个实验吗？这将清除当前结果并重新开始。')) {
      return;
    }

    // 检查实验是否使用了前端 API Key
    const experiment = experiments.find(exp => exp.id === id);
    if (experiment?.usedFrontendApiKey && !apiKey) {
      setRerunExperimentId(id);
      setShowApiKeyDialog(true);
      return;
    }

    try {
      await api.experiments.rerun(id, apiKey || '');
      fetchExperiments(); // 刷新列表
    } catch (error: any) {
      console.error('Error rerunning experiment:', error);
      if (error.message?.includes('API_KEY_REQUIRED') || error?.error === 'API_KEY_REQUIRED') {
        setRerunExperimentId(id);
        setShowApiKeyDialog(true);
      } else {
        alert('重新运行失败: ' + (error.message || 'Unknown error'));
      }
    }
  };

  const handleApiKeyConfirm = (apiKey: string) => {
    setShowApiKeyDialog(false);
    if (rerunExperimentId) {
      handleRerun(rerunExperimentId, apiKey);
      setRerunExperimentId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('确定要删除这个实验吗？此操作无法撤销！')) {
      return;
    }

    try {
      await api.experiments.delete(id);
      fetchExperiments(); // 刷新列表
    } catch (error) {
      console.error('Error deleting experiment:', error);
      alert('删除失败');
    }
  };

  if (loading && experiments.length === 0) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: '#64748b',
        fontSize: '14px'
      }}>
        <span className="animate-pulse">INITIALIZING SYSTEM...</span>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px 20px', maxWidth: '1000px', margin: '0 auto' }}>
      <header style={{ marginBottom: '48px' }}>
        <h1 style={{
          fontSize: '24px',
          fontWeight: 800,
          color: '#1e293b',
          letterSpacing: '-0.03em',
          marginBottom: '8px'
        }}>
          KONG <span style={{ color: '#3b82f6', fontWeight: 400 }}>RESEARCH</span>
        </h1>
        <p style={{ color: '#64748b', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Dynamic Halting & Recursive Knowledge Forge
        </p>
      </header>

      {!showCreateForm ? (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '14px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em', margin: 0 }}>
              Recent Experiments
            </h2>
            <button
              onClick={() => setShowCreateForm(true)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#1e293b',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#334155'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#1e293b'}
            >
              + Create New
            </button>
          </div>

          {experiments.length === 0 ? (
            <div style={{
              padding: '60px 40px',
              textAlign: 'center',
              border: '1px dashed #cbd5e1',
              borderRadius: '12px',
              backgroundColor: '#f1f5f9'
            }}>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '0' }}>
                NO ACTIVE EXPERIMENTS RESIDING IN DATABASE.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {experiments.map(exp => (
                <ExperimentListItem
                  key={exp.id}
                  experiment={exp}
                  onRerun={() => handleRerun(exp.id)}
                  onDelete={() => handleDelete(exp.id)}
                  onRefresh={fetchExperiments}
                />
              ))}
            </div>
          )}
        </div>
      ) : (
        <CreateExperimentForm
          onSuccess={handleCreateSuccess}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      <ApiKeyDialog
        open={showApiKeyDialog}
        onClose={() => {
          setShowApiKeyDialog(false);
          setRerunExperimentId(null);
        }}
        onConfirm={handleApiKeyConfirm}
        title="AUTH_REQUIRED"
        message="This experiment session was initiated with a temporary API Key. Provisioning a new key is required for execution restart."
      />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ExperimentList />} />
        <Route path="/experiments/:id" element={<ExperimentPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
