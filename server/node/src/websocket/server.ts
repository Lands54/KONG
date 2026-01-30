/**
 * WebSocket 服务器
 * 基础推送图更新消息
 */

import { Server as HTTPServer } from 'http';
import { WebSocketServer, WebSocket } from 'ws';

interface ExtWebSocket extends WebSocket {
  experimentId?: string;
}

let wss: WebSocketServer;

export function setupWebSocket(server: HTTPServer) {
  wss = new WebSocketServer({ server });

  wss.on('connection', (ws: ExtWebSocket) => {
    console.log('WebSocket client connected');

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

  console.log('WebSocket server ready');
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
