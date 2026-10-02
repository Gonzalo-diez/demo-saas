import { categories } from "@/types/categories";

function normalize(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, " ")
}

export function resolveCategory(input: string | null | undefined) {
  if (!input) return null

  const normalizedInput = normalize(input)

  return (
    categories.find((category) => {
      const candidates = [
        category.value,
        category.name,
        category.slug,
        ...(category.aliases ?? []),
      ]

      return candidates.some((candidate) => normalize(candidate) === normalizedInput)
    }) ?? null
  )
}