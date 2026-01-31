/**
 * API 配置
 * 统一管理所有 API 端点
 */

const API_CONFIG = {
  // 后端服务地址
  NODE_API_BASE: import.meta.env.VITE_NODE_API_URL || 'http://localhost:3000',
  PYTHON_API_BASE: import.meta.env.VITE_PYTHON_API_URL || 'http://localhost:8000',

  // API 端点
  ENDPOINTS: {
    // Node.js 服务端点
    EXPERIMENTS: '/api/experiments',
    EXPERIMENT_DETAIL: (id: string) => `/api/experiments/${id}`,
    EXPERIMENT_RERUN: (id: string) => `/api/experiments/${id}/rerun`,
    EXPERIMENT_DELETE: (id: string) => `/api/experiments/${id}`,
    EXPERIMENT_METRICS: (id: string) => `/api/experiments/${id}/metrics`,
    EXPERIMENT_CANCEL: (id: string) => `/api/experiments/${id}/cancel`,
    EXPERIMENT_EXPORT: (id: string) => `/api/experiments/${id}/export`,

    // Python 服务端点
    INFER: '/api/v1/infer',
    HEALTH: '/api/v1/health',
    CONFIG_CHECK: '/api/v1/config/check',
    CONFIG_INFO: '/api/v1/config/info',
    CONFIG_RELOAD: '/api/v1/config/reload',
    // 通用 DataSet API
    DATASETS: '/api/v1/datasets',
    DATASET_SPLITS: (datasetId: string) => `/api/v1/datasets/${datasetId}/splits`,
    DATASET_SAMPLES: (datasetId: string) => `/api/v1/datasets/${datasetId}/samples`,
    DATASET_SAMPLE: (datasetId: string, split: string, index: number) =>
      `/api/v1/datasets/${datasetId}/sample/${split}/${index}`,
    DEBUG_TEST_EXTRACTION: '/api/v1/debug/test-extraction',
    MODELS_CATALOG: '/api/v1/models/catalog',
  },

  // 请求配置
  TIMEOUT: 300000, // 5分钟
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1秒
};

export default API_CONFIG;

// 便捷函数
export const getNodeApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.NODE_API_BASE}${endpoint}`;
};

export const getPythonApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.PYTHON_API_BASE}${endpoint}`;
};
