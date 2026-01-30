/**
 * 分析路由
 * 支持实验对比和策略性能分析
 */

import { Router } from 'express';
import { PrismaClient } from '@prisma/client';

const router = Router();
const prisma = new PrismaClient();

/**
 * GET /api/analysis/compare
 * 对比多个实验
 * Query params: ids=id1,id2,id3
 */
router.get('/compare', async (req, res) => {
  try {
    const ids = (req.query.ids as string)?.split(',') || [];

    if (ids.length < 2) {
      return res.status(400).json({ error: 'At least 2 experiment IDs required' });
    }

    const experiments = await prisma.experiment.findMany({
      where: { id: { in: ids } },
      include: {
        nodes: true,
        data: true
      }
    });

    // 构建对比数据
    const comparison = experiments.map(exp => {
      const nodeCount = exp.nodes.length;

      // Extract trace from buckets
      const traceItem = exp.data.find(d => d.category === 'trace' && d.key === 'execution_trace');
      const trace: any[] = traceItem ? JSON.parse(traceItem.value) : [];

      const iterations = trace.length;
      const decisionStats = trace.reduce((acc: any, t) => {
        const action = t.action || 'UNKNOWN';
        acc[action] = (acc[action] || 0) + 1;
        return acc;
      }, {});

      // 解析统计信息
      let stats: any = {};
      try {
        if ((exp as any).graphBStats) stats.G_B = JSON.parse((exp as any).graphBStats);
        if ((exp as any).graphTStats) stats.G_T = JSON.parse((exp as any).graphTStats);
        if ((exp as any).graphFStats) stats.G_F = JSON.parse((exp as any).graphFStats);
      } catch (e) { }

      return {
        id: exp.id,
        name: exp.name,
        strategy: exp.haltingStrategy,
        nodeCount,
        iterations,
        decisionStats,
        stats
      };
    });

    res.json({ comparison });
  } catch (error) {
    console.error('Error comparing experiments:', error);
    res.status(500).json({ error: 'Failed to compare experiments' });
  }
});

/**
 * GET /api/analysis/strategy-performance
 * 策略性能分析
 * Query params: strategy (可选，指定策略)
 */
router.get('/strategy-performance', async (req, res) => {
  try {
    const strategy = req.query.strategy as string;

    const where: any = { status: 'completed' };
    if (strategy) {
      where.haltingStrategy = strategy;
    }

    const experiments = await prisma.experiment.findMany({
      where,
      include: {
        nodes: true,
        data: true
      }
    });

    // 按策略分组统计
    const performance: any = {};

    experiments.forEach(exp => {
      const strategy = exp.haltingStrategy;
      if (!performance[strategy]) {
        performance[strategy] = {
          count: 0,
          totalNodes: 0,
          totalIterations: 0,
          avgNodes: 0,
          avgIterations: 0,
          decisionDistribution: {}
        };
      }

      // Extract trace
      const traceItem = exp.data.find(d => d.category === 'trace' && d.key === 'execution_trace');
      const trace: any[] = traceItem ? JSON.parse(traceItem.value) : [];

      performance[strategy].count++;
      performance[strategy].totalNodes += exp.nodes.length;
      performance[strategy].totalIterations += trace.length;

      trace.forEach(t => {
        const action = t.action || 'UNKNOWN';
        const dist = performance[strategy].decisionDistribution;
        dist[action] = (dist[action] || 0) + 1;
      });
    });

    // 计算平均值
    Object.keys(performance).forEach(strategy => {
      const p = performance[strategy];
      p.avgNodes = p.totalNodes / p.count;
      p.avgIterations = p.totalIterations / p.count;
    });

    res.json({ performance });
  } catch (error) {
    console.error('Error analyzing strategy performance:', error);
    res.status(500).json({ error: 'Failed to analyze strategy performance' });
  }
});

export { router as analysisRouter };
