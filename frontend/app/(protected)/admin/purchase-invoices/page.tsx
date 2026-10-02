import { redirect } from "next/navigation";

// Ruta anterior: ahora vive como tab en /admin/purchases.
export default function LegacyRedirectPage() {
  redirect("/admin/purchases?tab=remitos");
}
