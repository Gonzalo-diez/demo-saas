"use client";

type BrandFilterProps = {
  value: string;
  brands: string[];
  onChange: (value: string) => void;
};

export function BrandFilter({ value, brands, onChange }: BrandFilterProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor="brand" className="text-sm font-medium">
        Marca
      </label>
      <select
        id="brand"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
      >
        <option value="">Todas las marcas</option>
        {brands.map((brand) => (
          <option key={brand} value={brand}>
            {brand}
          </option>
        ))}
      </select>
    </div>
  );
}