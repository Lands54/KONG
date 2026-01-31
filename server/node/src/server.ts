/**
 * Node.js Express 服务器
 */

// 加载环境变量（必须在其他导入之前）
import 'dotenv/config';

import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { experimentsRouter } from './routes/experiments';
import { metricsRouter } from './routes/metrics';
import { exportRouter } from './routes/export';
import { analysisRouter } from './routes/analysis';
import { setupWebSocket, broadcastLog } from './websocket/server';
import { handleError } from './utils/errorHandler';
import { logger } from './utils/logger';

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());

// 路由
app.use('/api/experiments', experimentsRouter);
app.use('/api/experiments', metricsRouter);
app.use('/api/experiments', exportRouter);
app.use('/api/analysis', analysisRouter);

// 内部日志转发 (来自 Python)
app.post('/api/internal/log', (req, res) => {
  const { experimentId, message, level, timestamp } = req.body;
  if (experimentId && message) {
    broadcastLog(experimentId, { message, level, timestamp });
  }
  res.status(200).send('OK');
});

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'node-api' });
});

// 创建 HTTP 服务器
const server = createServer(app);

// 设置 WebSocket（在 HTTP 服务器上）
setupWebSocket(server);

// 启动服务器
server.listen(PORT, () => {
  logger.info(`Node.js API server running on port ${PORT}`);
  console.log(`WebSocket server ready`);
});
