/**
 * 本地缓存工具
 * 使用 localStorage 缓存 API 数据
 */

const CACHE_PREFIX = 'dynhalting_';
const CACHE_VERSION = '1.0';

interface CacheItem<T> {
  data: T;
  timestamp: number;
  version: string;
}

// 缓存过期时间（毫秒）
const CACHE_EXPIRY = {
  files: 24 * 60 * 60 * 1000,      // 24小时
  samples: 60 * 60 * 1000,          // 1小时
  sampleDetail: 30 * 60 * 1000,     // 30分钟
};

function getCacheKey(key: string): string {
  return `${CACHE_PREFIX}${key}`;
}

function isExpired(item: CacheItem<any>, expiry: number): boolean {
  return Date.now() - item.timestamp > expiry;
}

export function setCache<T>(key: string, data: T, expiry: number = 60 * 60 * 1000): void {
  try {
    const item: CacheItem<T> = {
      data,
      timestamp: Date.now(),
      version: CACHE_VERSION
    };
    localStorage.setItem(getCacheKey(key), JSON.stringify(item));
  } catch (e) {
    console.warn('Failed to set cache:', e);
  }
}

export function getCache<T>(key: string, expiry?: number): T | null {
  try {
    const cached = localStorage.getItem(getCacheKey(key));
    if (!cached) return null;

    const item: CacheItem<T> = JSON.parse(cached);
    
    // 检查版本
    if (item.version !== CACHE_VERSION) {
      localStorage.removeItem(getCacheKey(key));
      return null;
    }

    // 检查过期
    if (expiry && isExpired(item, expiry)) {
      localStorage.removeItem(getCacheKey(key));
      return null;
    }

    return item.data;
  } catch (e) {
    console.warn('Failed to get cache:', e);
    return null;
  }
}

export function clearCache(key?: string): void {
  try {
    if (key) {
      localStorage.removeItem(getCacheKey(key));
    } else {
      // 清除所有缓存
      const keys = Object.keys(localStorage);
      keys.forEach(k => {
        if (k.startsWith(CACHE_PREFIX)) {
          localStorage.removeItem(k);
        }
      });
    }
  } catch (e) {
    console.warn('Failed to clear cache:', e);
  }
}

// 特定缓存函数
export const cache = {
  files: {
    get: () => getCache<any[]>('docred_files', CACHE_EXPIRY.files),
    set: (data: any[]) => setCache('docred_files', data, CACHE_EXPIRY.files),
    clear: () => clearCache('docred_files')
  },
  samples: {
    get: (file: string, page: number) => getCache<any>(`samples_${file}_${page}`, CACHE_EXPIRY.samples),
    set: (file: string, page: number, data: any) => setCache(`samples_${file}_${page}`, data, CACHE_EXPIRY.samples),
    clear: (file?: string) => {
      if (file) {
        // 清除特定文件的所有页
        const keys = Object.keys(localStorage);
        keys.forEach(k => {
          if (k.includes(`samples_${file}_`)) {
            localStorage.removeItem(k);
          }
        });
      } else {
        const keys = Object.keys(localStorage);
        keys.forEach(k => {
          if (k.startsWith(getCacheKey('samples_'))) {
            localStorage.removeItem(k);
          }
        });
      }
    }
  },
  sampleDetail: {
    get: (file: string, index: number) => getCache<any>(`sample_${file}_${index}`, CACHE_EXPIRY.sampleDetail),
    set: (file: string, index: number, data: any) => setCache(`sample_${file}_${index}`, data, CACHE_EXPIRY.sampleDetail),
    clear: (file?: string, index?: number) => {
      if (file && index !== undefined) {
        clearCache(`sample_${file}_${index}`);
      } else if (file) {
        const keys = Object.keys(localStorage);
        keys.forEach(k => {
          if (k.includes(`sample_${file}_`)) {
            localStorage.removeItem(k);
          }
        });
      } else {
        const keys = Object.keys(localStorage);
        keys.forEach(k => {
          if (k.startsWith(getCacheKey('sample_'))) {
            localStorage.removeItem(k);
          }
        });
      }
    }
  }
};
