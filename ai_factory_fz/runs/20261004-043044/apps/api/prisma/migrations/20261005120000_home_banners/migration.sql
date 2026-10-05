-- CreateTable
CREATE TABLE "home_banners" (
    "id" UUID NOT NULL,
    "title" VARCHAR(120) NOT NULL,
    "subtitle" VARCHAR(200),
    "image_url" VARCHAR(500) NOT NULL,
    "cta_label" VARCHAR(60) NOT NULL,
    "category_slug" VARCHAR(100),
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL,

    CONSTRAINT "home_banners_pkey" PRIMARY KEY ("id")
);
