/**
 * 指标路由
 */

import { Router } from 'express';
import { ExperimentService } from '../services/experiment_service';

const router = Router();
const experimentService = new ExperimentService();

/**
 * GET /api/experiments/:id/metrics
 * 获取实验指标
 */
router.get('/:id/metrics', async (req, res) => {
  try {
    const { id } = req.params;
    const metrics = await experimentService.getMetrics(id);
    
    if (!metrics) {
      return res.status(404).json({ error: 'Experiment not found' });
    }
    
    res.json(metrics);
  } catch (error) {
    console.error('Error getting metrics:', error);
    res.status(500).json({ error: 'Failed to get metrics' });
  }
});

export { router as metricsRouter };
