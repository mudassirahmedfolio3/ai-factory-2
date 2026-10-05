-- CreateTable
CREATE TABLE "bootstrap_meta" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "bootstrap_meta_pkey" PRIMARY KEY ("id")
);
