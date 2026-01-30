/**
 * 项目常量配置
 * 统一管理所有硬编码的默认值和配置参数
 */

// 默认参数配置
export const DEFAULT_MAX_DEPTH = 3;
export const DEFAULT_MAX_NODES = 50;
export const DEFAULT_MAX_ITERATIONS = 10;
export const DEFAULT_SIMILARITY_THRESHOLD = 0.9;

// API 配置
export const DEFAULT_API_TIMEOUT = 300000; // 5分钟（毫秒）
export const DEFAULT_PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';
export const DEFAULT_NODE_API_PORT = process.env.PORT || 3000;

// 判停策略默认值
export const DEFAULT_HALTING_STRATEGY = 'RULE_BASED';

// 实验状态
export const EXPERIMENT_STATUS = {
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const;

// 缓存配置
export const CACHE_EXPIRY = {
  FILES: 24 * 60 * 60 * 1000,      // 24小时
  SAMPLES: 60 * 60 * 1000,          // 1小时
  SAMPLE_DETAIL: 30 * 60 * 1000,    // 30分钟
} as const;
