"use client";

import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createProductSchema,
  type CreateProductFormInput,
  type CreateProductFormValues,
} from "@/features/admin/products/schemas/product-schema";
import { useCreateProduct } from "@/features/admin/products/hooks/use-create-product";
import { useUpdateProduct } from "@/features/admin/products/hooks/use-update-product";
import { useUploadProductImage } from "@/features/admin/products/hooks/use-upload-product-image";
import type { Product } from "@/features/admin/products/types";
import { ProductCategorySelect } from "@/features/admin/products/components/product-category-select";
import { isUnclassifiedCategory } from "@/features/admin/products/utils/category-utils";

const INVALID_BRANDS = new Set(["pendiente", "sin marca"]);

type CreateProductFormProps = {
  onSuccess?: () => void;
  mode?: "create" | "edit";
  initialData?: Product | null;
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(value) ? 0 : value);
}

export function CreateProductForm({
  onSuccess,
  mode = "create",
  initialData = null,
}: CreateProductFormProps) {
  const createProduct = useCreateProduct();
  const updateProduct = useUpdateProduct();
  const uploadProductImage = useUploadProductImage();
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    setError,
    formState: { errors },
  } = useForm<CreateProductFormInput, undefined, CreateProductFormValues>({
    resolver: zodResolver(createProductSchema),
    defaultValues: {
      sku: "",
      name: "",
      description: null,
      brand: null,
      category: null,
      image_url: null,
      unit_cost: 0,
      unit_price: 0,
      stock_current: 0,
      stock_min: 0,
    },
  });

  const unitCost = Number(watch("unit_cost") ?? 0);
  const unitPrice = Number(watch("unit_price") ?? 0);
  const imageUrl = watch("image_url");
  const unitMargin = useMemo(() => unitPrice - unitCost, [unitPrice, unitCost]);

  useEffect(() => {
    if (mode === "edit" && initialData) {
      reset({
        sku: initialData.sku,
        name: initialData.name,
        description: initialData.description ?? "",
        brand: initialData.brand ?? "",
        category: initialData.category ?? "",
        image_url: initialData.image_url ?? "",
        unit_cost: Number(initialData.unit_cost),
        unit_price: Number(initialData.unit_price),
        stock_current: initialData.stock_current,
        stock_min: initialData.stock_min,
      });
      return;
    }

    reset({
      sku: "",
      name: "",
      description: null,
      brand: null,
      category: null,
      image_url: null,
      unit_cost: 0,
      unit_price: 0,
      stock_current: 0,
      stock_min: 0,
    });
  }, [mode, initialData, reset]);

  const handleImageUpload = async (file: File) => {
    try {
      const res = await uploadProductImage.mutateAsync(file);

      // 👇 guardás la URL subida en el form
      setValue("image_url", res.url, {
        shouldValidate: true,
        shouldDirty: true,
      });

      toast.success("Imagen subida correctamente");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al subir imagen");
    }
  };

  const onSubmit = async (data: CreateProductFormValues) => {
    const brand = data.brand?.trim() || null;
    const category = data.category?.trim() || null;

    // El backend rechaza crear productos sin marca o sin categoría (quedarían
    // incompletos), así que lo avisamos acá en vez de devolver un 400 genérico.
    // En edición se permite guardar un producto que sigue "Sin clasificar".
    if (mode === "create") {
      let hasError = false;

      if (!brand || INVALID_BRANDS.has(brand.toLowerCase())) {
        setError("brand", { message: "La marca es obligatoria" });
        hasError = true;
      }

      if (!category || isUnclassifiedCategory(category)) {
        setError("category", {
          message: "Elegí una categoría o creá una nueva",
        });
        hasError = true;
      }

      if (hasError) return;
    }

    const payload = {
      ...data,
      description: data.description?.trim() || null,
      brand,
      // En edición, sin categoría elegida no la tocamos (evita mandar null).
      category: mode === "edit" ? (category ?? undefined) : category,
      image_url: data.image_url?.trim() || null,
      unit_cost: Number(data.unit_cost),
      unit_price: Number(data.unit_price),
      stock_current: Number(data.stock_current),
      stock_min: Number(data.stock_min),
    };

    try {
      if (mode === "edit" && initialData) {
        await updateProduct.mutateAsync({
          productId: initialData.id,
          data: payload,
        });

        toast.success("Producto actualizado correctamente", {
          position: "top-right",
          duration: 4000,
        });

        onSuccess?.();
        return;
      }

      await createProduct.mutateAsync(payload);

      toast.success("Producto creado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      reset({
        sku: "",
        name: "",
        description: null,
        brand: null,
        category: null,
        image_url: null,
        unit_cost: 0,
        unit_price: 0,
        stock_current: 0,
        stock_min: 0,
      });

      onSuccess?.();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Error desconocido";

      toast.error(
        mode === "edit"
          ? `Error al actualizar: ${errorMessage}`
          : `Error al crear: ${errorMessage}`,
        {
          position: "top-right",
          duration: 5000,
        },
      );
    }
  };

  const isPending = createProduct.isPending || updateProduct.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 sm:space-y-6">
      <section className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">SKU</label>
            <Input {...register("sku")} placeholder="Ej: SKU-001" />
            {errors.sku && (
              <p className="text-sm text-destructive">{errors.sku.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Nombre</label>
            <Input {...register("name")} placeholder="Nombre del producto" />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-sm font-medium">Descripción</label>
          <Textarea
            {...register("description")}
            placeholder="Descripción breve del producto"
            rows={4}
            className="min-h-28"
          />
          {errors.description && (
            <p className="text-sm text-destructive">
              {errors.description.message}
            </p>
          )}
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border p-4">
        <div className="space-y-1">
          <h5 className="text-sm font-semibold">Clasificación</h5>
          <p className="text-xs text-muted-foreground">
            Información para identificar y agrupar el producto.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Marca{mode === "create" ? " *" : ""}
            </label>
            <Input {...register("brand")} placeholder="Marca" />
            {errors.brand && (
              <p className="text-sm text-destructive">{errors.brand.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Categoría{mode === "create" ? " *" : ""}
            </label>
            <ProductCategorySelect
              value={watch("category")}
              onChange={(value) =>
                setValue("category", value, {
                  shouldValidate: true,
                  shouldDirty: true,
                })
              }
            />
            {errors.category && (
              <p className="text-sm text-destructive">
                {errors.category.message}
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border p-4">
        <div className="space-y-1">
          <h5 className="text-sm font-semibold">Inventario, costo y precio</h5>
          <p className="text-xs text-muted-foreground">
            Datos base para stock, costo de compra y precio de venta.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Costo unitario</label>
            <Input
              type="number"
              step="0.01"
              min="0"
              {...register("unit_cost")}
            />
            {errors.unit_cost && (
              <p className="text-sm text-destructive">
                {errors.unit_cost.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Precio de venta</label>
            <Input
              type="number"
              step="0.01"
              min="0"
              {...register("unit_price")}
            />
            {errors.unit_price && (
              <p className="text-sm text-destructive">
                {errors.unit_price.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Stock actual</label>
            <Input type="number" min="0" {...register("stock_current")} />
            {errors.stock_current && (
              <p className="text-sm text-destructive">
                {errors.stock_current.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Stock mínimo</label>
            <Input type="number" min="0" {...register("stock_min")} />
            {errors.stock_min && (
              <p className="text-sm text-destructive">
                {errors.stock_min.message}
              </p>
            )}
          </div>
        </div>

        <div className="rounded-xl border bg-muted/30 p-4">
          <p className="text-sm font-medium">Resumen unitario</p>
          <div className="mt-2 grid gap-3 text-sm md:grid-cols-3">
            <div>
              <span className="text-muted-foreground">Costo:</span>{" "}
              <span className="font-medium">{formatCurrency(unitCost)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Venta:</span>{" "}
              <span className="font-medium">{formatCurrency(unitPrice)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Margen unitario:</span>{" "}
              <span className="font-medium">{formatCurrency(unitMargin)}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Seccion de la Imagen del Producto Modificada */}
      <section className="space-y-4 rounded-2xl border p-4">
        <div className="space-y-1">
          <p className="text-sm font-semibold">Imagen del producto</p>
          <p className="text-xs text-muted-foreground">
            Sube un archivo local o introduce una URL web directa.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 items-end">
          {/* Opción 1: Subir Archivo */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Opción 1: Subir desde el dispositivo
            </label>
            <Input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleImageUpload(file);
                }
              }}
            />
          </div>

          {/* Opción 2: URL de la imagen */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Opción 2: Pegar URL de la imagen
            </label>
            <Input
              type="url"
              placeholder="https://ejemplo.com/imagen.jpg"
              {...register("image_url")}
            />
          </div>
        </div>

        {uploadProductImage.isPending && (
          <p className="text-sm text-muted-foreground animate-pulse">
            Subiendo archivo de imagen...
          </p>
        )}

        {errors.image_url && (
          <p className="text-sm text-destructive">{errors.image_url.message}</p>
        )}

        {/* Preview de la Imagen */}
        {Boolean(imageUrl) ? (
          <div className="overflow-hidden rounded-2xl border bg-muted relative group">
            <img
              src={imageUrl || ""}
              alt="Preview del producto"
              className="h-64 w-full object-cover"
              onError={(e) => {
                // Previene que se rompa la UI si la URL ingresada es inválida
                (e.target as HTMLImageElement).src =
                  "https://placehold.co/600x400?text=URL+de+Imagen+Invalida";
              }}
            />
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed bg-muted/30">
            <p className="text-sm text-muted-foreground">
              No hay imagen ni URL seleccionada
            </p>
          </div>
        )}

        {Boolean(imageUrl) && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() =>
              setValue("image_url", "", {
                shouldValidate: true,
                shouldDirty: true,
                shouldTouch: true,
              })
            }
          >
            Limpiar imagen / URL
          </Button>
        )}
      </section>

      <div className="flex flex-col gap-4 rounded-2xl border p-4 md:flex-row md:items-center md:justify-between">
        <Button type="submit" disabled={isPending} className="w-full md:w-auto">
          {isPending
            ? mode === "edit"
              ? "Guardando..."
              : "Creando..."
            : mode === "edit"
              ? "Guardar cambios"
              : "Crear producto"}
        </Button>
      </div>
    </form>
  );
}