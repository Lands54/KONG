/**
 * 实验服务的单元测试
 */

import { ExperimentService } from '../../../backend/node_service/src/services/experiment_service';

describe('ExperimentService', () => {
  let service: ExperimentService;

  beforeEach(() => {
    service = new ExperimentService();
  });

  describe('createExperiment', () => {
    it('should create an experiment with valid data', async () => {
      const data = {
        name: 'Test Experiment',
        goal: 'Test goal',
        initialEvidence: 'Test text',
        haltingStrategy: 'RULE_BASED',
      };

      // Mock Prisma and API calls
      const experiment = await service.createExperiment(data);
      expect(experiment).toBeDefined();
    });
  });

  describe('getExperiment', () => {
    it('should return experiment by id', async () => {
      // Mock implementation
      const experiment = await service.getExperiment('test-id');
      expect(experiment).toBeDefined();
    });
  });
});
