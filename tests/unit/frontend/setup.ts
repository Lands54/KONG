import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// 清理每个测试后的 DOM
afterEach(() => {
  cleanup();
});
