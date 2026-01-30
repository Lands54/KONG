/**
 * 统一 API 客户端
 * 封装所有 API 调用，统一错误处理和重试逻辑
 */

import API_CONFIG, { getNodeApiUrl, getPythonApiUrl } from '../config/api';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private retryAttempts: number;
  private retryDelay: number;

  constructor(
    baseUrl: string,
    timeout: number = API_CONFIG.TIMEOUT,
    retryAttempts: number = API_CONFIG.RETRY_ATTEMPTS,
    retryDelay: number = API_CONFIG.RETRY_DELAY
  ) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
    this.retryAttempts = retryAttempts;
    this.retryDelay = retryDelay;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          error: 'Unknown error',
          message: response.statusText
        }));

        throw new Error(errorData.message || errorData.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      clearTimeout(timeoutId);

      // 如果是网络错误且还有重试次数，进行重试
      if (
        (error.name === 'TypeError' || error.name === 'AbortError') &&
        retryCount < this.retryAttempts
      ) {
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.request<T>(endpoint, options, retryCount + 1);
      }

      throw error;
    }
  }

  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    // 安全地序列化数据，处理循环引用
    let body: string | undefined;
    if (data) {
      try {
        body = this.safeStringify(data);
      } catch (error: any) {
        console.error('Failed to stringify request data:', error);
        throw new Error(`Failed to serialize request data: ${error.message}`);
      }
    }

    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * 安全地序列化对象，处理循环引用
   */
  private safeStringify(obj: any): string {
    const seen = new WeakSet();

    return JSON.stringify(obj, (key, value) => {
      // 跳过函数和 undefined
      if (typeof value === 'function' || value === undefined) {
        return undefined;
      }

      // 跳过 DOM 元素和 React 相关对象
      if (value && typeof value === 'object') {
        if (value instanceof HTMLElement ||
          value instanceof Event ||
          value.constructor?.name === 'FiberNode' ||
          value.constructor?.name === 'SyntheticEvent') {
          return '[Object]';
        }

        // 检查循环引用
        if (seen.has(value)) {
          return '[Circular Reference]';
        }

        seen.add(value);
      }

      return value;
    });
  }

  async put<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    // 安全地序列化数据，处理循环引用
    let body: string | undefined;
    if (data) {
      try {
        body = this.safeStringify(data);
      } catch (error: any) {
        console.error('Failed to stringify request data:', error);
        throw new Error(`Failed to serialize request data: ${error.message}`);
      }
    }

    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body,
    });
  }

  async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// 创建 API 客户端实例
export const nodeApiClient = new ApiClient(API_CONFIG.NODE_API_BASE);
export const pythonApiClient = new ApiClient(API_CONFIG.PYTHON_API_BASE);

// 便捷函数
export const api = {
  // Node.js API
  experiments: {
    list: () => nodeApiClient.get(API_CONFIG.ENDPOINTS.EXPERIMENTS),
    get: (id: string) => nodeApiClient.get(API_CONFIG.ENDPOINTS.EXPERIMENT_DETAIL(id)),
    create: (data: any) => nodeApiClient.post(API_CONFIG.ENDPOINTS.EXPERIMENTS, data),
    rerun: (id: string, apiKey?: string) =>
      nodeApiClient.post(API_CONFIG.ENDPOINTS.EXPERIMENT_RERUN(id), { apiKey }),
    delete: (id: string) => nodeApiClient.delete(API_CONFIG.ENDPOINTS.EXPERIMENT_DELETE(id)),
    metrics: (id: string) => nodeApiClient.get(API_CONFIG.ENDPOINTS.EXPERIMENT_METRICS(id)),
    export: (id: string) => nodeApiClient.get(API_CONFIG.ENDPOINTS.EXPERIMENT_EXPORT(id)),
  },

  // Python API
  inference: {
    run: (data: any) => pythonApiClient.post(API_CONFIG.ENDPOINTS.INFER, data),
    health: () => pythonApiClient.get(API_CONFIG.ENDPOINTS.HEALTH),
  },

  config: {
    check: () => pythonApiClient.get(API_CONFIG.ENDPOINTS.CONFIG_CHECK),
    info: () => pythonApiClient.get(API_CONFIG.ENDPOINTS.CONFIG_INFO),
    reload: () => pythonApiClient.post(API_CONFIG.ENDPOINTS.CONFIG_RELOAD),
  },

  datasets: {
    list: () => pythonApiClient.get(API_CONFIG.ENDPOINTS.DATASETS),
    splits: (datasetId: string) => pythonApiClient.get(API_CONFIG.ENDPOINTS.DATASET_SPLITS(datasetId)),
    samples: (datasetId: string, split: string, page: number = 1, pageSize: number = 20) =>
      pythonApiClient.get(
        `${API_CONFIG.ENDPOINTS.DATASET_SAMPLES(datasetId)}?split=${encodeURIComponent(split)}&page=${page}&page_size=${pageSize}`
      ),
    sample: (datasetId: string, split: string, index: number) =>
      pythonApiClient.get(API_CONFIG.ENDPOINTS.DATASET_SAMPLE(datasetId, split, index)),
  },

  // Component Discovery API (SSOT)
  components: {
    fetchCatalog: () => pythonApiClient.get(API_CONFIG.ENDPOINTS.MODELS_CATALOG),
  },

  debug: {
    testExtraction: (data: any) =>
      pythonApiClient.post(API_CONFIG.ENDPOINTS.DEBUG_TEST_EXTRACTION, data),
  },
};

