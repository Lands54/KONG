/**
 * WebSocket Hook
 * 基础 WebSocket 连接，接收图更新消息
 */

import { useEffect, useRef, useState } from 'react';

// WebSocket 使用与 HTTP 相同的端口
const WS_URL = `ws://${window.location.hostname}:3000`;

export function useWebSocket(experimentId: string | undefined) {
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!experimentId) return;

    // 连接到 WebSocket 服务器
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      
      // 订阅实验
      ws.send(JSON.stringify({
        type: 'subscribe',
        experimentId
      }));
    };

    ws.onmessage = (event) => {
      setLastMessage(event);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [experimentId]);

  return { lastMessage, connected };
}
