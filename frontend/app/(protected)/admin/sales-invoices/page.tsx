import { redirect } from "next/navigation";

// Ruta anterior: ahora vive como tab en /admin/sales.
export default function LegacyRedirectPage() {
  redirect("/admin/sales?tab=remitos");
}
