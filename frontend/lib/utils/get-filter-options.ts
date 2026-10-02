type Product = {
  brand: string;
};

export function getBrandOptions(products: Product[]) {
  return [...new Set(products.map((p) => p.brand))].sort((a, b) =>
    a.localeCompare(b)
  );
}