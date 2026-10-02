"use client"

type Props = {
  quantity: number
  onDecrease: () => void
  onIncrease: () => void
}

export function QuantityStepper({ quantity, onDecrease, onIncrease }: Props) {
  return (
    <div className="flex w-full items-center gap-2">
      <button
        type="button"
        onClick={onDecrease}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border text-sm transition-colors hover:bg-muted sm:h-10 sm:w-10"
        aria-label="Disminuir cantidad"
      >
        -
      </button>

      <div className="flex h-9 min-w-0 flex-1 items-center justify-center rounded-md border px-3 text-sm sm:h-10 sm:text-base">
        {quantity}
      </div>

      <button
        type="button"
        onClick={onIncrease}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border text-sm transition-colors hover:bg-muted sm:h-10 sm:w-10"
        aria-label="Aumentar cantidad"
      >
        +
      </button>
    </div>
  )
}