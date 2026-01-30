/**
 * 节点渲染器
 * 基础状态高亮：
 * - 绿色：HALT-ACCEPT
 * - 灰色：HALT-DROP
 * - 黄色：HITL
 * - 默认：LOOP
 */

export function getNodeStatus(node: any): string {
  const metadata = node.metadata || {};
  return metadata.status || 'LOOP';
}

export function getNodeColor(status: string): string {
  switch (status) {
    case 'HALT-ACCEPT':
      return '#4caf50'; // 绿色
    case 'HALT-DROP':
      return '#9e9e9e'; // 灰色
    case 'HITL':
      return '#ffc107'; // 黄色
    case 'LOOP':
      return '#2196f3'; // 蓝色
    default:
      return '#e8e8e8'; // 默认灰色
  }
}
