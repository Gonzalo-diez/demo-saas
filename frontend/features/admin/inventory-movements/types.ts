export type InventoryMovementType =
  | "purchase"
  | "purchase_reversal"
  | "sale"
  | "sale_reversal"
  | "adjustment_in"
  | "adjustment_out"
  | "inventory_found"
  | "inventory_loss"
  | "initial_stock";

export type InventoryReferenceType =
  | "purchase_invoice"
  | "sales_invoice"
  | "order"
  | "manual_adjustment"
  | "draft"
  | "import";

export type InventoryMovementProduct = {
  id: number;
  name: string;
  sku: string | null;
};

export type InventoryMovementCreator = {
  id: number;
  name: string;
  email: string;
};

export type InventoryMovement = {
  id: number;
  product_id: number;
  movement_type: InventoryMovementType;
  quantity: number;
  stock_before: number;
  stock_after: number;
  unit_cost: string | null;
  unit_price: string | null;
  reference_type: InventoryReferenceType | null;
  reference_id: number | null;
  notes: string | null;
  created_by: number | null;
  created_at: string;
  product?: InventoryMovementProduct | null;
  creator?: InventoryMovementCreator | null;
};

export type InventoryMovementsResponse = {
  items: InventoryMovement[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type InventoryMovementsQueryParams = {
  page?: number;
  page_size?: number;
  product_id?: number | null;
  movement_type?: InventoryMovementType | "all";
  reference_type?: InventoryReferenceType | "all";
};

export type ProductInventoryMovementsParams = {
  productId: number;
  page?: number;
  page_size?: number;
};