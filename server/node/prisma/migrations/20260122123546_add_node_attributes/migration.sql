-- AlterTable
ALTER TABLE "Node" ADD COLUMN "confidence" REAL;
ALTER TABLE "Node" ADD COLUMN "haltReason" TEXT;
ALTER TABLE "Node" ADD COLUMN "nodeMetadata" TEXT;
ALTER TABLE "Node" ADD COLUMN "status" TEXT;
ALTER TABLE "Node" ADD COLUMN "structuralImportance" REAL;
ALTER TABLE "Node" ADD COLUMN "uncertainty" REAL;

-- CreateIndex
CREATE INDEX "Node_status_idx" ON "Node"("status");
