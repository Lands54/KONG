-- CreateTable
CREATE TABLE "Experiment" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "goal" TEXT NOT NULL,
    "initialEvidence" TEXT NOT NULL,
    "haltingStrategy" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'running',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "graphB" TEXT,
    "graphT" TEXT,
    "graphF" TEXT,
    "graphBStats" TEXT,
    "graphTStats" TEXT,
    "graphFStats" TEXT
);

-- CreateTable
CREATE TABLE "Node" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "experimentId" TEXT NOT NULL,
    "nodeId" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "level" INTEGER NOT NULL DEFAULT 0,
    "isHalted" BOOLEAN NOT NULL DEFAULT false,
    "ablationValue" REAL,
    "parentNodeId" TEXT,
    "source" TEXT,
    "semanticEmbedding" TEXT,
    CONSTRAINT "Node_experimentId_fkey" FOREIGN KEY ("experimentId") REFERENCES "Experiment" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Decision" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "experimentId" TEXT NOT NULL,
    "iteration" INTEGER NOT NULL,
    "decision" TEXT NOT NULL,
    "tokenCount" INTEGER,
    "reasoningTrace" TEXT,
    "uncertaintyVar" REAL,
    "nodeValues" TEXT,
    CONSTRAINT "Decision_experimentId_fkey" FOREIGN KEY ("experimentId") REFERENCES "Experiment" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "Experiment_status_idx" ON "Experiment"("status");

-- CreateIndex
CREATE INDEX "Experiment_createdAt_idx" ON "Experiment"("createdAt");

-- CreateIndex
CREATE INDEX "Node_experimentId_idx" ON "Node"("experimentId");

-- CreateIndex
CREATE INDEX "Node_parentNodeId_idx" ON "Node"("parentNodeId");

-- CreateIndex
CREATE INDEX "Node_source_idx" ON "Node"("source");

-- CreateIndex
CREATE INDEX "Decision_experimentId_idx" ON "Decision"("experimentId");

-- CreateIndex
CREATE INDEX "Decision_iteration_idx" ON "Decision"("iteration");
