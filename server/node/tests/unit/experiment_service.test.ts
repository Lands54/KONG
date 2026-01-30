
import { ExperimentService } from '../../src/services/experiment_service';

// Mock Prisma Client
jest.mock('@prisma/client', () => ({
    PrismaClient: jest.fn(() => ({
        experiment: {
            findUnique: jest.fn(),
            create: jest.fn(),
            update: jest.fn(),
            delete: jest.fn(),
            findMany: jest.fn(),
        },
        experimentData: {
            createMany: jest.fn(),
        },
        node: {
            createMany: jest.fn(),
        }
    }))
}));

// Mock axios
jest.mock('axios');

describe('ExperimentService', () => {
    let service: ExperimentService;
    let mockPrisma: any;

    beforeEach(() => {
        service = new ExperimentService();
        // Capture the mock instance created by the service
        const { PrismaClient } = require('@prisma/client');
        // usage: new PrismaClient() -> returns the object from factory.
        // mock.results contains { type: 'return', value: ... }
        const res = (PrismaClient as any).mock.results[0];
        mockPrisma = res ? res.value : undefined;
        console.log('Captured mockPrisma:', !!mockPrisma);

        // If undefined, maybe it hasn't been instantiated yet?
        // ExperimentService instantiates at top level.
        // Jest runs imports before test body.
        if (!mockPrisma) {
            // Fallback: create one to see if it works for late binding?
            // No, if service uses a different one, we fail.
            // Maybe we need to re-require the service under test in beforeEach?
            // jest.resetModules();
        }

        // jest.clearAllMocks(); // DO NOT CLEAR: wipes constructor results
    });

    describe('getExperiment', () => {
        it('should parse buckets correctly into structured result', async () => {
            const mockExperiment = {
                id: 'exp1',
                name: 'Test Experiment',
                finalGraph: null,
                data: [
                    { category: 'graph', key: 'G_B', value: '{"nodes":[]}' },
                    { category: 'trace', key: 'execution_trace', value: '[{"action":"EXPAND"}]' },
                    { category: 'metric', key: 'accuracy', value: '0.95' },
                ]
            };

            mockPrisma.experiment.findUnique.mockResolvedValue(mockExperiment);

            const result = await service.getExperiment('exp1');

            expect(result).toBeDefined();
            expect(result!.intermediate_graphs['G_B']).toEqual({ nodes: [] });
            expect(result!.trace).toHaveLength(1);
            expect(result!.trace[0].action).toEqual('EXPAND');
            expect(result!.metrics['accuracy']).toEqual(0.95);
        });

        it('should handle missing experimentation', async () => {
            mockPrisma.experiment.findUnique.mockResolvedValue(null);
            const result = await service.getExperiment('invalid');
            expect(result).toBeNull();
        });
    });
});
