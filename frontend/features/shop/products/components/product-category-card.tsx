import Link from "next/link";
import Image from "next/image";
import { ChevronRight } from "lucide-react";

type Props = {
  title: string;
  description?: string;
  href: string;
  image_url?: string;
  count?: number;
  ageRestricted?: boolean;
};

export function ProductCategoryCard({
  title,
  description,
  href,
  image_url,
  count,
  ageRestricted,
}: Props) {
  return (
    <Link
      href={href}
      className="group block h-full overflow-hidden rounded-3xl bg-card ring-[1.5px] ring-border transition-all hover:-translate-y-0.5 hover:shadow-md"
    >
      <article className="flex h-full flex-col">
        {/* Usamos bg-card (o bg-white) para integrar todo el fondo de la tarjeta */}
        <div className="relative aspect-square w-full overflow-hidden bg-card p-4 sm:aspect-[4/3]">
          {image_url ? (
            <Image
              src={image_url}
              alt={title}
              fill
              loading="eager"
              unoptimized={!image_url.startsWith("https://res.cloudinary.com/")}
              className="object-contain p-2 mix-blend-multiply transition-transform duration-300 group-hover:scale-105"
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <svg
                className="h-10 w-10 text-brand/40"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1}
                aria-hidden="true"
              >
                <rect
                  x="3"
                  y="3"
                  width="18"
                  height="18"
                  rx="2"
                  strokeWidth="1.5"
                />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" strokeWidth="1.5" />
              </svg>
            </div>
          )}

          {/* Badges */}
          {typeof count === "number" && (
            <span className="absolute left-3 top-3 z-10 rounded-full bg-muted/80 px-3 py-1 text-xs font-semibold text-foreground backdrop-blur">
              {count} productos
            </span>
          )}

          {ageRestricted && (
            <span className="absolute right-3 top-3 z-10 rounded-full bg-stamp px-2.5 py-1 text-xs font-bold text-stamp-foreground">
              +18
            </span>
          )}
        </div>

        {/* Cuerpo */}
        <div className="flex flex-1 flex-col p-4 sm:p-5 pt-0 sm:pt-0">
          <h3 className="font-heading text-lg font-bold sm:text-xl">{title}</h3>

          {description && (
            <p className="mt-2 line-clamp-2 text-sm text-muted-foreground sm:text-base">
              {description}
            </p>
          )}

          <div className="mt-auto pt-4 flex items-center gap-1.5 text-sm font-semibold text-brand">
            <span>Ver catálogo</span>
            <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </div>
        </div>
      </article>
    </Link>
  );
}