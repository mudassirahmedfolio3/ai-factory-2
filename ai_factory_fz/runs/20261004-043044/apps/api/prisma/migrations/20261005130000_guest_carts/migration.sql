-- Guest cart persistence for X-Guest-Cart-Id (WI-014)

-- CreateTable
CREATE TABLE "guest_carts" (
    "id" UUID NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL,

    CONSTRAINT "guest_carts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "guest_cart_items" (
    "id" UUID NOT NULL,
    "guest_cart_id" UUID NOT NULL,
    "variant_id" UUID NOT NULL,
    "quantity" INTEGER NOT NULL DEFAULT 1,
    "unit_price_cents" INTEGER NOT NULL,
    "currency" VARCHAR(3) NOT NULL DEFAULT 'GBP',
    "product_name" VARCHAR(200) NOT NULL,
    "variant_label" VARCHAR(120) NOT NULL,
    "sku" VARCHAR(64) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL,

    CONSTRAINT "guest_cart_items_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "guest_carts_expires_at_idx" ON "guest_carts"("expires_at");

-- CreateIndex
CREATE INDEX "guest_cart_items_guest_cart_id_idx" ON "guest_cart_items"("guest_cart_id");

-- CreateIndex
CREATE UNIQUE INDEX "guest_cart_items_guest_cart_id_variant_id_key" ON "guest_cart_items"("guest_cart_id", "variant_id");

-- AddForeignKey
ALTER TABLE "guest_cart_items" ADD CONSTRAINT "guest_cart_items_guest_cart_id_fkey" FOREIGN KEY ("guest_cart_id") REFERENCES "guest_carts"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "guest_cart_items" ADD CONSTRAINT "guest_cart_items_variant_id_fkey" FOREIGN KEY ("variant_id") REFERENCES "product_variants"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
