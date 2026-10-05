"use client";

import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToggleProductVisibility } from "@/features/admin/products/hooks/use-toggle-product-visibility";
import type { Product } from "@/features/admin/products/types";

type Props = {
  product: Product;
  className?: string;
  size?: "sm" | "default";
};

/** Publica u oculta un producto del catálogo de la tienda. */
export function ProductVisibilityButton({ product, className, size = "sm" }: Props) {
  const toggle = useToggleProductVisibility();
  const isToggling = toggle.isPending && toggle.variables?.productId === product.id;

  return (
    <Button
      type="button"
      variant="outline"
      size={size}
      className={className}
      disabled={isToggling}
      onClick={() => toggle.mutate({ productId: product.id, isPublic: !product.is_public })}
    >
      {product.is_public ? <EyeOff className="mr-2 h-4 w-4" /> : <Eye className="mr-2 h-4 w-4" />}
      {isToggling ? "Guardando..." : product.is_public ? "Ocultar" : "Publicar"}
    </Button>
  );
}
