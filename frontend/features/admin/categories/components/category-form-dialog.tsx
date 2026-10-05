"use client";

import { useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  categorySchema,
  type CategoryFormValues,
} from "@/features/admin/categories/schemas/category-schema";
import {
  useCreateCategory,
  useUpdateCategory,
} from "@/features/admin/categories/hooks/use-category-mutations";
import { useUploadCategoryImage } from "@/features/admin/categories/hooks/use-upload-category-image";
import type { Category } from "@/features/admin/categories/types";

type CategoryFormProps = {
  category?: Category | null;
  onDone: () => void;
};

function CategoryForm({ category, onDone }: CategoryFormProps) {
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();
  const isEdit = !!category;
  const uploadImage = useUploadCategoryImage();
  const isPending = createCategory.isPending || updateCategory.isPending;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: category?.name ?? "",
      description: category?.description ?? "",
      image_url: category?.image_url ?? "",
      is_public: category?.is_public ?? true,
      requires_age_verification: category?.requires_age_verification ?? false,
    },
  });

  const imageUrl = watch("image_url");

  const handleImageUpload = async (file: File) => {
    try {
      const res = await uploadImage.mutateAsync(file);
      setValue("image_url", res.url, {
        shouldValidate: true,
        shouldDirty: true,
      });
      toast.success("Imagen subida correctamente");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Error al subir la imagen",
      );
    }
  };

  const onSubmit = async (values: CategoryFormValues) => {
    const data = {
      name: values.name,
      description: values.description || null,
      image_url: values.image_url || null,
      is_public: values.is_public,
      requires_age_verification: values.requires_age_verification,
    };

    try {
      if (category) {
        await updateCategory.mutateAsync({ categoryId: category.id, data });
      } else {
        await createCategory.mutateAsync(data);
      }
      onDone();
    } catch {
      // el toast de error lo muestra el hook
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="category-name">Nombre *</Label>
        <Input
          id="category-name"
          placeholder="Ej: Bebidas"
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="category-description">Descripción</Label>
        <Textarea
          id="category-description"
          rows={3}
          placeholder="Se muestra en la tienda debajo del nombre."
          {...register("description")}
        />
        {errors.description && (
          <p className="text-sm text-destructive">
            {errors.description.message}
          </p>
        )}
      </div>

      <section className="space-y-3 rounded-2xl border p-4">
        <div className="space-y-1">
          <p className="text-sm font-semibold">Imagen de la categoría</p>
          <p className="text-xs text-muted-foreground">
            Es la portada que ven tus clientes en el catálogo. Subí un archivo o
            pegá una URL. Es obligatoria para publicar la categoría.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label
              htmlFor="category-image-file"
              className="text-xs text-muted-foreground"
            >
              Subir desde el dispositivo
            </Label>
            <Input
              id="category-image-file"
              type="file"
              accept="image/*"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) handleImageUpload(file);
              }}
            />
          </div>

          <div className="space-y-1.5">
            <Label
              htmlFor="category-image-url"
              className="text-xs text-muted-foreground"
            >
              O pegar la URL de la imagen
            </Label>
            <Input
              id="category-image-url"
              type="url"
              placeholder="https://ejemplo.com/imagen.jpg"
              {...register("image_url")}
            />
          </div>
        </div>

        {uploadImage.isPending && (
          <p className="animate-pulse text-sm text-muted-foreground">
            Subiendo imagen...
          </p>
        )}

        {errors.image_url && (
          <p className="text-sm text-destructive">{errors.image_url.message}</p>
        )}

        {imageUrl ? (
          <div className="space-y-2">
            <div className="overflow-hidden rounded-2xl border bg-card p-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imageUrl}
                alt="Vista previa de la categoría"
                className="h-40 w-full object-contain p-2 mix-blend-multiply"
                onError={(event) => {
                  (event.target as HTMLImageElement).src =
                    "https://placehold.co/600x300?text=URL+de+imagen+invalida";
                }}
              />
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                setValue("image_url", "", {
                  shouldValidate: true,
                  shouldDirty: true,
                })
              }
            >
              Quitar imagen
            </Button>
          </div>
        ) : (
          <div className="flex h-24 items-center justify-center rounded-2xl border border-dashed bg-muted/30">
            <p className="text-sm text-muted-foreground">
              Todavía no hay imagen
            </p>
          </div>
        )}
      </section>

      <div className="space-y-3 rounded-2xl border bg-muted/40 p-4">
        <label className="flex cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 accent-[var(--brand)]"
            {...register("is_public")}
          />
          <span className="text-sm">
            <span className="font-semibold">Publicar en el catálogo</span>
            <span className="block text-muted-foreground">
              Si la desmarcás, sus productos quedan solo para venta B2B interna.
            </span>
          </span>
        </label>

        <label className="flex cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 accent-[var(--brand)]"
            {...register("requires_age_verification")}
          />
          <span className="text-sm">
            <span className="font-semibold">
              Requiere verificación de edad (+18)
            </span>
            <span className="block text-muted-foreground">
              Los pedidos online con estos productos piden DNI y confirmar
              mayoría de edad.
            </span>
          </span>
        </label>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={onDone}
          disabled={isPending}
        >
          Cancelar
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending
            ? "Guardando..."
            : isEdit
              ? "Guardar cambios"
              : "Crear categoría"}
        </Button>
      </div>
    </form>
  );
}

type CategoryFormDialogProps = {
  /** Si viene, el diálogo edita esa categoría; si no, crea una nueva. */
  category?: Category | null;
  /** Modo controlado (edición desde la tabla). */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** Botón que abre el diálogo (modo no controlado, para crear). */
  trigger?: ReactNode;
};

export function CategoryFormDialog({
  category,
  open: controlledOpen,
  onOpenChange,
  trigger,
}: CategoryFormDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {category ? "Editar categoría" : "Nueva categoría"}
          </DialogTitle>
          <DialogDescription>
            Las categorías organizan tus productos y el catálogo que ven tus
            clientes.
          </DialogDescription>
        </DialogHeader>

        {/* Se monta recién al abrir: siempre arranca con los datos actuales */}
        <CategoryForm category={category} onDone={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
