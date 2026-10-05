"use client";

import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CategoriesList } from "@/features/admin/categories/components/categories-list";
import { CategoryFormDialog } from "@/features/admin/categories/components/category-form-dialog";

export default function CategoriesPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-2xl font-bold">Categorías</h2>
          <p className="text-sm text-muted-foreground">
            Organizá tus productos y elegí qué categorías ven tus clientes en el catálogo.
          </p>
        </div>

        <CategoryFormDialog
          trigger={
            <Button className="w-full sm:w-auto">
              <Plus className="mr-2 h-4 w-4" />
              Nueva categoría
            </Button>
          }
        />
      </div>

      <CategoriesList />
    </div>
  );
}
