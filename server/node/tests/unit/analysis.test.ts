
import request from 'supertest';
import express from 'express';
import { analysisRouter } from '../../src/routes/analysis';

// Setup mock for Prisma Client
jest.mock('@prisma/client', () => {
    return {
        PrismaClient: jest.fn(() => ({
            experiment: {
                findMany: jest.fn(),
            }
        }))
    };
});

const app = express();
app.use('/api/analysis', analysisRouter);

describe('Analysis Routes', () => {
    let mockPrisma: any;

    beforeEach(() => {
        const { PrismaClient } = require('@prisma/client');
        // Note: analysisRouter creates 'prisma' at module level when imported.
        const res = (PrismaClient as any).mock.results[0];
        mockPrisma = res ? res.value : undefined;
        // jest.clearAllMocks(); // DO NOT CLEAR: it wipes the constructor results needed to access the singleton
    });

    describe('GET /api/analysis/compare', () => {
        it('should aggregate stats from trace buckets', async () => {
            // Mock data
            const mockExperiments = [
                {
                    id: 'exp1',
                    name: 'Exp 1',
                    nodes: [{}, {}], // 2 nodes
                    data: [
                        {
                            category: 'trace',
                            key: 'execution_trace',
                            value: JSON.stringify([
                                { action: 'EXPAND' },
                                { action: 'HALT' }
                            ])
                        }
                    ]
                }
            ];

            mockPrisma.experiment.findMany.mockResolvedValue(mockExperiments);

            const res = await request(app).get('/api/analysis/compare?ids=exp1,exp2');

            expect(res.status).toBe(200);
            expect(res.body.comparison).toHaveLength(1);

            const stat = res.body.comparison[0];
            expect(stat.iterations).toBe(2);
            expect(stat.decisionStats['EXPAND']).toBe(1);
            expect(stat.decisionStats['HALT']).toBe(1);
        });
    });

    describe('GET /api/analysis/strategy-performance', () => {
        it('should group by strategy and count metrics', async () => {
            const mockExperiments = [
                {
                    haltingStrategy: 'rule_based',
                    nodes: [{}, {}],
                    data: [
                        {
                            category: 'trace',
                            key: 'execution_trace',
                            value: JSON.stringify([{ action: 'EXPAND' }])
                        }
                    ]
                }
            ];

            mockPrisma.experiment.findMany.mockResolvedValue(mockExperiments);

            const res = await request(app).get('/api/analysis/strategy-performance');
            expect(res.status).toBe(200);
            expect(res.body.performance['rule_based']).toBeDefined();
            expect(res.body.performance['rule_based'].count).toBe(1);
            expect(res.body.performance['rule_based'].totalIterations).toBe(1);
        });
    });
});
