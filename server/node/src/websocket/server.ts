/**
 * WebSocket 服务器
 * 基础推送图更新消息
 */

import { Server as HTTPServer } from 'http';
import { WebSocketServer, WebSocket } from 'ws';

interface ExtWebSocket extends WebSocket {
  experimentId?: string;
  isAlive?: boolean;
}

let wss: WebSocketServer;
let heartbeatInterval: NodeJS.Timeout;

export function setupWebSocket(server: HTTPServer) {
  wss = new WebSocketServer({ server });

  wss.on('connection', (ws: ExtWebSocket) => {
    console.log('WebSocket client connected');
    ws.isAlive = true;

    // 监听 pong 响应
    ws.on('pong', () => {
      ws.isAlive = true;
    });

    ws.on('message', (message: string) => {
      try {
        const data = JSON.parse(message.toString());

        // 处理客户端消息（如订阅实验）
        if (data.type === 'subscribe' && data.experimentId) {
          ws.experimentId = data.experimentId;
          ws.send(JSON.stringify({
            type: 'subscribed',
            experimentId: data.experimentId
          }));
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });

    ws.on('close', () => {
      console.log('WebSocket client disconnected');
    });
  });

  // 心跳检测：每 30 秒发送 ping，清理死连接
  heartbeatInterval = setInterval(() => {
    wss.clients.forEach((ws: ExtWebSocket) => {
      if (ws.isAlive === false) {
        console.log('Terminating dead WebSocket connection');
        return ws.terminate();
      }

      ws.isAlive = false;
      ws.ping();
    });
  }, 30000);

  console.log('WebSocket server ready with heartbeat monitoring');
}

/**
 * 广播图更新消息
 */
export function broadcastGraphUpdate(experimentId: string, data: any) {
  if (!wss) return;

  const message = JSON.stringify({
    type: 'graph_update',
    experimentId,
    data
  });

  wss.clients.forEach((client: ExtWebSocket) => {
    if (client.readyState === WebSocket.OPEN && client.experimentId === experimentId) {
      client.send(message);
    }
  });
}

/**
 * 广播决策消息
 */
export function broadcastDecision(experimentId: string, decision: any) {
  if (!wss) return;

  const message = JSON.stringify({
    type: 'decision',
    experimentId,
    decision
  });

  wss.clients.forEach((client: ExtWebSocket) => {
    if (client.readyState === WebSocket.OPEN && client.experimentId === experimentId) {
      client.send(message);
    }
  });
}

/**
 * 广播状态更新消息
 */
export function broadcastStatusUpdate(experimentId: string, status: string) {
  if (!wss) return;

  const message = JSON.stringify({
    type: 'status_update',
    experimentId,
    status
  });

  wss.clients.forEach((client: ExtWebSocket) => {
    if (client.readyState === WebSocket.OPEN && client.experimentId === experimentId) {
      client.send(message);
    }
  });
}
/**
 * 广播通用遥测事件 (LOG 或 TELEMETRY)
 */
export function broadcastEvent(experimentId: string, event: { type: string, payload: any, timestamp?: number }) {
  if (!wss) return;

  const message = JSON.stringify({
    type: event.type === 'TELEMETRY' ? 'telemetry' : 'log', // 统一前端 type
    experimentId,
    data: event.payload,
    timestamp: event.timestamp || Date.now()
  });

  wss.clients.forEach((client: ExtWebSocket) => {
    if (client.readyState === WebSocket.OPEN && client.experimentId === experimentId) {
      client.send(message);
    }
  });
}
