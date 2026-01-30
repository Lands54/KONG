/**
 * 数据导出路由
 */

import { Router } from 'express';
import { ExperimentService } from '../services/experiment_service';

const router = Router();
const experimentService = new ExperimentService();

/**
 * GET /api/experiments/:id/export
 * 导出完整实验数据（JSON）
 */
router.get('/:id/export', async (req, res) => {
  try {
    const { id } = req.params;
    const format = req.query.format as string || 'json';
    
    const experiment = await experimentService.getExperiment(id);
    
    if (!experiment) {
      return res.status(404).json({ error: 'Experiment not found' });
    }
    
    if (format === 'csv') {
      // CSV 导出
      const csv = experimentService.exportToCSV(experiment);
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename="experiment_${id}.csv"`);
      return res.send(csv);
    } else {
      // JSON 导出（默认）
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', `attachment; filename="experiment_${id}.json"`);
      return res.json(experiment);
    }
  } catch (error) {
    console.error('Error exporting experiment:', error);
    res.status(500).json({ error: 'Failed to export experiment' });
  }
});

export { router as exportRouter };
