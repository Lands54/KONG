/*
  Warnings:

  - You are about to drop the `Decision` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the column `graphB` on the `Experiment` table. All the data in the column will be lost.
  - You are about to drop the column `graphBStats` on the `Experiment` table. All the data in the column will be lost.
  - You are about to drop the column `graphF` on the `Experiment` table. All the data in the column will be lost.
  - You are about to drop the column `graphFStats` on the `Experiment` table. All the data in the column will be lost.
  - You are about to drop the column `graphT` on the `Experiment` table. All the data in the column will be lost.
  - You are about to drop the column `graphTStats` on the `Experiment` table. All the data in the column will be lost.
  - You are about to drop the column `ablationValue` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `confidence` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `haltReason` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `isHalted` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `nodeMetadata` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `semanticEmbedding` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `source` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `status` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `structuralImportance` on the `Node` table. All the data in the column will be lost.
  - You are about to drop the column `uncertainty` on the `Node` table. All the data in the column will be lost.

*/
-- DropIndex
DROP INDEX "Decision_iteration_idx";

-- DropIndex
DROP INDEX "Decision_experimentId_idx";

-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "Decision";
PRAGMA foreign_keys=on;

-- CreateTable
CREATE TABLE "ExperimentData" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "experimentId" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    CONSTRAINT "ExperimentData_experimentId_fkey" FOREIGN KEY ("experimentId") REFERENCES "Experiment" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Experiment" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "goal" TEXT NOT NULL,
    "initialEvidence" TEXT NOT NULL,
    "haltingStrategy" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'running',
    "usedFrontendApiKey" BOOLEAN NOT NULL DEFAULT false,
    "datasetId" TEXT,
    "datasetSplit" TEXT,
    "datasetIndex" INTEGER,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "finalGraph" TEXT
);
INSERT INTO "new_Experiment" ("createdAt", "datasetId", "datasetIndex", "datasetSplit", "goal", "haltingStrategy", "id", "initialEvidence", "name", "status", "updatedAt", "usedFrontendApiKey") SELECT "createdAt", "datasetId", "datasetIndex", "datasetSplit", "goal", "haltingStrategy", "id", "initialEvidence", "name", "status", "updatedAt", "usedFrontendApiKey" FROM "Experiment";
DROP TABLE "Experiment";
ALTER TABLE "new_Experiment" RENAME TO "Experiment";
CREATE INDEX "Experiment_status_idx" ON "Experiment"("status");
CREATE INDEX "Experiment_createdAt_idx" ON "Experiment"("createdAt");
CREATE TABLE "new_Node" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "experimentId" TEXT NOT NULL,
    "nodeId" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "level" INTEGER NOT NULL DEFAULT 0,
    "attributes" TEXT NOT NULL DEFAULT '{}',
    "metrics" TEXT NOT NULL DEFAULT '{}',
    "state" TEXT NOT NULL DEFAULT '{}',
    "parentNodeId" TEXT,
    CONSTRAINT "Node_experimentId_fkey" FOREIGN KEY ("experimentId") REFERENCES "Experiment" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_Node" ("experimentId", "id", "label", "level", "nodeId", "parentNodeId") SELECT "experimentId", "id", "label", "level", "nodeId", "parentNodeId" FROM "Node";
DROP TABLE "Node";
ALTER TABLE "new_Node" RENAME TO "Node";
CREATE INDEX "Node_experimentId_idx" ON "Node"("experimentId");
CREATE INDEX "Node_parentNodeId_idx" ON "Node"("parentNodeId");
CREATE INDEX "Node_label_idx" ON "Node"("label");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;

-- CreateIndex
CREATE INDEX "ExperimentData_experimentId_idx" ON "ExperimentData"("experimentId");

-- CreateIndex
CREATE INDEX "ExperimentData_category_idx" ON "ExperimentData"("category");

-- CreateIndex
CREATE INDEX "ExperimentData_key_idx" ON "ExperimentData"("key");
