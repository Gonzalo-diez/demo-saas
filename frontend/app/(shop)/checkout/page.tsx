import type { Metadata } from "next"
import { Suspense } from "react"
import { CheckoutPageClient } from "@/features/shop/cart/components/checkout-page-client"
import { RequireClientAuth } from "@/features/shop/auth/components/require-client-auth"

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: "Checkout | Distri Choco",
    description: "Revisá tu pedido antes de enviarlo.",
  }
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={null}>
      <RequireClientAuth>
        <CheckoutPageClient />
      </RequireClientAuth>
    </Suspense>
  )
}