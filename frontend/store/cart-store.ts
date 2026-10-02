"use client";

import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { ShopProduct } from "@/features/shop/products/types"

type CartItem = ShopProduct & {
  quantity: number
}

type CartStore = {
  items: CartItem[]
  addItem: (product: ShopProduct) => void
  removeItem: (productId: number) => void
  decreaseItem: (productId: number) => void
  deleteItem: (productId: number) => void
  clearCart: () => void
  getTotalItems: () => number
  getTotalPrice: () => number
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],

      addItem: (product) => {
        const items = get().items
        const existing = items.find((item) => item.id === product.id)

        if (existing) {
          set({
            items: items.map((item) =>
              item.id === product.id
                ? { ...item, quantity: item.quantity + 1 }
                : item
            ),
          })
          return
        }

        set({
          items: [...items, { ...product, quantity: 1 }],
        })
      },

      removeItem: (productId) => {
        const items = get().items
        const target = items.find((item) => item.id === productId)

        if (!target) return

        if (target.quantity <= 1) {
          set({
            items: items.filter((item) => item.id !== productId),
          })
          return
        }

        set({
          items: items.map((item) =>
            item.id === productId
              ? { ...item, quantity: item.quantity - 1 }
              : item
          ),
        })
      },

      decreaseItem: (productId) => {
        const items = get().items
        const target = items.find((item) => item.id === productId)

        if (!target) return

        if (target.quantity === 1) {
          set({
            items: items.filter((item) => item.id !== productId),
          })
          return
        }

        set({
          items: items.map((item) =>
            item.id === productId
              ? { ...item, quantity: item.quantity - 1 }
              : item
          ),
        })
      },

      deleteItem: (productId) => {
        set({
          items: get().items.filter((item) => item.id !== productId),
        })
      },

      clearCart: () => set({ items: [] }),

      getTotalItems: () =>
        get().items.reduce((acc, item) => acc + item.quantity, 0),

      getTotalPrice: () =>
        get().items.reduce((acc, item) => acc + item.unit_price * item.quantity, 0),
    }),
    {
      name: "cart-storage",
    }
  )
)