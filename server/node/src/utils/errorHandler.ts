/**
 * 统一错误处理
 * 规范化错误处理和响应
 */

import { Response } from 'express';
import { logger } from './logger';

export interface ApiError {
  code: string;
  message: string;
  statusCode: number;
  details?: any;
}

export class AppError extends Error {
  public code: string;
  public statusCode: number;
  public details?: any;

  constructor(code: string, message: string, statusCode: number = 500, details?: any) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    Error.captureStackTrace(this, this.constructor);
  }
}

export function handleError(error: any, res: Response): void {
  logger.error('Error occurred:', error);

  if (error instanceof AppError) {
    res.status(error.statusCode).json({
      error: error.code,
      message: error.message,
      details: error.details
    });
    return;
  }

  // 处理已知错误类型
  if (error.name === 'ValidationError') {
    res.status(400).json({
      error: 'VALIDATION_ERROR',
      message: error.message || 'Validation failed'
    });
    return;
  }

  if (error.name === 'NotFoundError') {
    res.status(404).json({
      error: 'NOT_FOUND',
      message: error.message || 'Resource not found'
    });
    return;
  }

  // 默认错误响应
  res.status(500).json({
    error: 'INTERNAL_SERVER_ERROR',
    message: error.message || 'An unexpected error occurred'
  });
}

export function asyncHandler(fn: Function) {
  return (req: any, res: any, next: any) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
