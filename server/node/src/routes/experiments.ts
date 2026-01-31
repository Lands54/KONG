/**
 * 实验路由
 */

import { Router } from 'express';
import type { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { ExperimentService } from '../services/experiment_service';
import { logger } from '../utils/logger';
import { handleError, asyncHandler } from '../utils/errorHandler';

const router = Router();
const experimentService = new ExperimentService();
const prisma = new PrismaClient();

/**
 * POST /api/experiments
 * 创建实验并启动推理
 */
router.post('/', asyncHandler(async (req: Request, res: Response) => {
  const { name, goal, text, haltingStrategy, orchestrator, components, apiKey, datasetRef } = req.body;

  if (!goal || !text) {
    return res.status(400).json({ error: 'goal and text are required' });
  }

  const experiment = await experimentService.createExperiment({
    name: name || `Experiment ${Date.now()}`,
    goal,
    initialEvidence: text,
    haltingStrategy: haltingStrategy || 'RULE_BASED',
    orchestrator: orchestrator, // 传递编排器ID
    components: components,     // 传递组件配置
    apiKey: apiKey,  // 传递 API Key
    datasetRef: datasetRef  // 可选：数据集溯源
  });

  res.json(experiment);
}));

/**
 * GET /api/experiments/:id
 * 获取实验详情（包含图结构）
 */
router.get('/:id', asyncHandler(async (req: Request, res: Response) => {
  const { id } = req.params;
  const experiment = await experimentService.getExperiment(id);

  if (!experiment) {
    return res.status(404).json({ error: 'Experiment not found' });
  }

  res.json(experiment);
}));

/**
 * GET /api/experiments
 * 获取实验列表
 */
router.get('/', asyncHandler(async (req: Request, res: Response) => {
  const experiments = await experimentService.listExperiments();
  res.json(experiments);
}));

/**
 * POST /api/experiments/:id/cancel
 * 取消实验
 */
router.post('/:id/cancel', asyncHandler(async (req: Request, res: Response) => {
  const { id } = req.params;
  const result = await experimentService.cancelExperiment(id);
  res.json(result);
}));

/**
 * POST /api/experiments/:id/rerun
 * 重新运行实验
 */
router.post('/:id/rerun', asyncHandler(async (req: Request, res: Response) => {
  const { id } = req.params;
  const { apiKey } = req.body;

  // 检查原实验是否使用了前端 API Key
  const originalExperiment = await prisma.experiment.findUnique({
    where: { id },
    select: { usedFrontendApiKey: true }
  });

  if (originalExperiment?.usedFrontendApiKey) {
    // 如果原实验使用了前端 API Key，必须提供新的 API Key
    if (!apiKey || !apiKey.trim()) {
      return res.status(400).json({
        error: 'API_KEY_REQUIRED',
        message: '此实验创建时使用了前端传入的 API Key，重新运行时必须提供 API Key'
      });
    }
  }

  const experiment = await experimentService.rerunExperiment(id, apiKey);
  res.json(experiment);
}));

/**
 * DELETE /api/experiments/:id
 * 删除实验
 */
router.delete('/:id', asyncHandler(async (req: Request, res: Response) => {
  const { id } = req.params;
  await experimentService.deleteExperiment(id);
  res.json({ success: true });
}));

export { router as experimentsRouter };
