/*
  Warnings:

  - You are about to drop the column `apiKeyEncrypted` on the `Experiment` table. All the data in the column will be lost.

*/
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
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "graphB" TEXT,
    "graphT" TEXT,
    "graphF" TEXT,
    "graphBStats" TEXT,
    "graphTStats" TEXT,
    "graphFStats" TEXT
);
INSERT INTO "new_Experiment" ("createdAt", "goal", "graphB", "graphBStats", "graphF", "graphFStats", "graphT", "graphTStats", "haltingStrategy", "id", "initialEvidence", "name", "status", "updatedAt") SELECT "createdAt", "goal", "graphB", "graphBStats", "graphF", "graphFStats", "graphT", "graphTStats", "haltingStrategy", "id", "initialEvidence", "name", "status", "updatedAt" FROM "Experiment";
DROP TABLE "Experiment";
ALTER TABLE "new_Experiment" RENAME TO "Experiment";
CREATE INDEX "Experiment_status_idx" ON "Experiment"("status");
CREATE INDEX "Experiment_createdAt_idx" ON "Experiment"("createdAt");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
