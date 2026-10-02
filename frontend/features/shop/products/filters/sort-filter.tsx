"use client";

type SortFilterProps = {
  value: string;
  onChange: (value: string) => void;
};

export function SortFilter({ value, onChange }: SortFilterProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor="sort" className="text-sm font-medium">
        Ordenar por
      </label>
      <select
        id="sort"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50"
      >
        <option value="">Destacados</option>
        <option value="name-asc">Nombre A–Z</option>
        <option value="name-desc">Nombre Z–A</option>
        <option value="price-asc">Precio: menor a mayor</option>
        <option value="price-desc">Precio: mayor a menor</option>
      </select>
    </div>
  );
}