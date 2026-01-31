/**
 * 实验服务 (Upgraded: Pan-Graph Result Protocol)
 * 调用 Python FastAPI，将全量实验数据存入 ExperimentData
 */

import { PrismaClient } from '@prisma/client';
import axios from 'axios';
import { DEFAULT_PYTHON_API_URL, DEFAULT_MAX_DEPTH, DEFAULT_MAX_NODES, DEFAULT_MAX_ITERATIONS } from '../config/constants';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();
const PYTHON_API_URL = DEFAULT_PYTHON_API_URL;

/**
 * 通用序列化函数
 */
function safeStringify(obj: any): string {
  const seen = new WeakSet();
  return JSON.stringify(obj, (key, value) => {
    if (typeof value === 'function' || value === undefined) return undefined;
    if (typeof value === 'object' && value !== null) {
      if (seen.has(value)) return '[Circular]';
      seen.add(value);
    }
    return value;
  });
}

export class ExperimentService {
  /**
   * 创建实验记录
   */
  async createExperiment(data: {
    name: string;
    goal: string;
    initialEvidence: string;
    haltingStrategy: string;
    orchestrator?: string;      // 新增
    components?: any;           // 新增
    apiKey?: string;
    datasetRef?: { datasetId: string; split: string; index: number } | null;
  }) {
    const experiment = await prisma.experiment.create({
      data: {
        name: data.name,
        goal: data.goal,
        initialEvidence: data.initialEvidence,
        haltingStrategy: data.haltingStrategy,
        status: 'running',
        usedFrontendApiKey: !!(data.apiKey && data.apiKey.trim()),
        datasetId: data.datasetRef?.datasetId ?? null,
        datasetSplit: data.datasetRef?.split ?? null,
        datasetIndex: data.datasetRef?.index ?? null
      }
    });

    // 异步执行
    this.runInferenceAsync(experiment.id, data).catch(err => {
      logger.error(`Experiment ${experiment.id} runtime error:`, err);
    });

    return experiment;
  }

  /**
   * 核心推理任务 (Pan-Graph Protocol 版)
   */
  private async runInferenceAsync(experimentId: string, data: {
    goal: string;
    initialEvidence: string;
    haltingStrategy: string;
    orchestrator?: string;      // 新增
    components?: any;           // 新增
    apiKey?: string;
  }) {
    try {
      const payload = {
        goal: data.goal,
        text: data.initialEvidence,
        orchestrator: data.orchestrator || 'dynamic_halting', // 传递编排器
        components: data.components || {},                    // 传递组件配置
        halting_strategy: data.haltingStrategy,
        max_depth: DEFAULT_MAX_DEPTH,
        max_nodes: DEFAULT_MAX_NODES,
        max_iterations: DEFAULT_MAX_ITERATIONS,
        api_key: data.apiKey,
        experiment_id: experimentId
      };

      const response = await axios.post(`${PYTHON_API_URL}/api/v1/infer`, payload, { timeout: 300000 });
      const result = response.data;

      // 1. 存储全量桶数据 (ExperimentData)
      const dataToCreate: any[] = [];

      // A. Graphs 桶
      if (result.intermediate_graphs) {
        for (const [key, graphObj] of Object.entries(result.intermediate_graphs)) {
          dataToCreate.push({
            experimentId,
            category: 'graph',
            key: key,
            value: safeStringify(graphObj)
          });
        }
      }

      // B. Trace 桶
      if (result.trace) {
        dataToCreate.push({
          experimentId,
          category: 'trace',
          key: 'execution_trace',
          value: safeStringify(result.trace)
        });
      }

      // C. Metrics 桶
      if (result.metrics) {
        for (const [key, val] of Object.entries(result.metrics)) {
          dataToCreate.push({
            experimentId,
            category: 'metric',
            key: key,
            value: typeof val === 'object' ? safeStringify(val) : String(val)
          });
        }
      }

      // D. Metadata/Config 桶
      if (result.metadata) {
        dataToCreate.push({
          experimentId,
          category: 'metadata',
          key: 'runtime_metadata',
          value: safeStringify(result.metadata)
        });
      }

      // E. Stats 桶 (New: Telemetry)
      if (result.intermediate_stats) {
        dataToCreate.push({
          experimentId,
          category: 'stats',
          key: 'intermediate_telemetry',
          value: safeStringify(result.intermediate_stats)
        });
      }

      // F. Logs 桶 (New: Log Persistence)
      if (result.logs) {
        dataToCreate.push({
          experimentId,
          category: 'logs',
          key: 'execution_logs',
          value: safeStringify(result.logs)
        });
      }

      // 执行批量创建
      if (dataToCreate.length > 0) {
        await prisma.experimentData.createMany({ data: dataToCreate });
      }

      // 2. 存储核心节点数据 (Node 表，用于快速检索/视图)
      if (result.graph?.nodes) {
        const nodes = Object.values(result.graph.nodes).map((node: any) => {
          // 确保 slots 存在，防止 Python端返回旧格式
          const attributes = node.attributes || {};
          const metrics = node.metrics || {};
          const state = node.state || {};

          // 兼容性：如果 metadata 还在，合并进 attributes 用于溯源
          if (node.metadata) {
            attributes._meta = node.metadata;
          }
          // 兼容旧字段：如果 node.level 或 status 没在 state 里 (理论上 Python 端如果不改 orchestrator 可能还没放进去)
          // 但我们的 Node 类做了兼容，to_dict 暴露了 slots。
          // 这里还是做个防御性编程，如果 level 不在 state 里，尝试从顶层拿
          const level = state.level ?? node.level ?? 0;
          const parentNodeId = state.parentNodeId ?? node.parentNodeId ?? null;

          return {
            experimentId,
            nodeId: node.id,
            label: node.label || attributes.label || 'Unknown', // 优先用顶层兼容字段
            level: Number(level),
            parentNodeId: parentNodeId,

            // Slots (JSON Stringified)
            attributes: safeStringify(attributes),
            metrics: safeStringify(metrics),
            state: safeStringify(state)
          };
        });

        await prisma.node.createMany({ data: nodes });
      }

      // 3. 更新主表状态
      const finalStatus = result.status; // 直接使用 Python 结果，支持 'cancelled'
      await prisma.experiment.update({
        where: { id: experimentId },
        data: {
          status: finalStatus,
          finalGraph: safeStringify(result.graph)
        }
      });

      // 4. WebSocket 推送
      const { broadcastStatusUpdate, broadcastGraphUpdate } = await import('../websocket/server');
      broadcastStatusUpdate(experimentId, finalStatus);
      if (result.graph) broadcastGraphUpdate(experimentId, result.graph);

    } catch (error: any) {
      logger.error(`Inference failed for ${experimentId}:`, error.message);
      await prisma.experiment.update({
        where: { id: experimentId },
        data: { status: 'failed' }
      });
      const { broadcastStatusUpdate } = await import('../websocket/server');
      broadcastStatusUpdate(experimentId, 'failed');
    }
  }

  /**
   * 取消实验
   */
  async cancelExperiment(id: string) {
    try {
      const response = await axios.post(`${PYTHON_API_URL}/api/v1/cancel/${id}`);
      // 本地状态更新交由 runInferenceAsync 的回调处理，或者在这里预先设为 stopping?
      // 鉴于 Python 端响应很快，这里主要负责触发。
      return response.data;
    } catch (error: any) {
      logger.error(`Failed to cancel experiment ${id}:`, error.message);
      throw error;
    }
  }

  /**
   * 获取实验详情 (适配新协议)
   */
  async getExperiment(id: string) {
    const experiment = await prisma.experiment.findUnique({
      where: { id },
      include: {
        nodes: true,
        data: true
      }
    });

    if (!experiment) return null;

    // 重构结果对象
    const intermediate_graphs: Record<string, any> = {};
    const intermediate_stats: Record<string, any> = {};
    const metrics: Record<string, any> = {};
    const trace: any[] = [];
    const logs: any[] = [];

    // 从 ExperimentData 中提取数据
    experiment.data.forEach(item => {
      try {
        const parsed = JSON.parse(item.value);
        if (item.category === 'graph') {
          intermediate_graphs[item.key] = parsed;
        } else if (item.category === 'stats') {
          Object.assign(intermediate_stats, parsed);
        } else if (item.category === 'metric') {
          metrics[item.key] = parsed;
        } else if (item.category === 'trace') {
          trace.push(...(Array.isArray(parsed) ? parsed : [parsed]));
        } else if (item.category === 'logs') {
          logs.push(...(Array.isArray(parsed) ? parsed : [parsed]));
        }
      } catch {
        // 容错处理字符串
        if (item.category === 'metric') metrics[item.key] = item.value;
      }
    });

    return {
      ...experiment,
      graph: experiment.finalGraph ? JSON.parse(experiment.finalGraph) : null,
      intermediate_graphs,
      intermediate_stats,
      metrics,
      trace,
      logs
    };
  }

  /**
   * 其他基础方法保持不变但适配新模型
   */
  async listExperiments() {
    return await prisma.experiment.findMany({
      orderBy: { createdAt: 'desc' },
      select: { id: true, name: true, goal: true, status: true, createdAt: true }
    });
  }

  async deleteExperiment(id: string) {
    await prisma.experiment.delete({ where: { id } });
    return { success: true };
  }

  // --- Stubs to fix build errors ---
  async rerunExperiment(id: string, apiKey?: string) {
    logger.warn('rerunExperiment not implemented');
    return this.getExperiment(id);
  }

  exportToCSV(experiment: any) {
    return "id,name,status\n" + `${experiment.id},${experiment.name},${experiment.status}`;
  }

  async getMetrics(id: string) {
    const experiment = await this.getExperiment(id);
    return experiment?.metrics || {};
  }
}
