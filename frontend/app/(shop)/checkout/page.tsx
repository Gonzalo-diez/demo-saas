import type { Metadata } from "next"
import { Suspense } from "react"
import { CheckoutPageClient } from "@/features/shop/cart/components/checkout-page-client"

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: "Checkout",
    description: "Revisá tu pedido antes de enviarlo.",
  }
}

// El carrito se ve sin cuenta; el formulario del pedido (y el registro / login) aparece
// dentro de CheckoutPageClient recién cuando el visitante va a finalizar la compra.
export default function CheckoutPage() {
  return (
    <Suspense fallback={null}>
      <CheckoutPageClient />
    </Suspense>
  )
}
