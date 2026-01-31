/**
 * WebSocket Hook
 * 基础 WebSocket 连接，接收图更新消息
 */

import { useEffect, useRef, useState } from 'react';

// WebSocket 使用与 HTTP 相同的端口
const WS_URL = `ws://${window.location.hostname}:3000`;

// 添加类型定义
export interface StandardEvent {
  type: 'log' | 'telemetry' | 'graph_update' | 'status_update';
  experimentId: string;
  data: any;
  timestamp?: number;
}

export function useWebSocket(experimentId: string | undefined) {
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [lastEvent, setLastEvent] = useState<StandardEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = () => {
    if (!experimentId) return;

    // 清理旧连接
    if (wsRef.current) {
      wsRef.current.close();
    }

    // 连接到 WebSocket 服务器
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      reconnectAttemptsRef.current = 0; // 重置重连计数

      // 订阅实验
      ws.send(JSON.stringify({
        type: 'subscribe',
        experimentId
      }));
    };

    ws.onmessage = (event) => {
      setLastMessage(event);
      try {
        const parsed = JSON.parse(event.data);
        // 标准化事件结构
        setLastEvent(parsed);
      } catch (e) {
        // ignore non-json messages
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);

      // 自动重连（指数退避）
      const delay = Math.min(
        1000 * Math.pow(2, reconnectAttemptsRef.current),
        30000 // 最大延迟 30 秒
      );

      console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1})`);

      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current++;
        connect();
      }, delay);
    };
  };

  useEffect(() => {
    connect();

    return () => {
      // 清理重连定时器
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      // 关闭连接
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [experimentId]);

  return { lastMessage, lastEvent, connected };
}
