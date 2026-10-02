"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "checkout_customer_data";

export type StoredCheckoutData = {
  customer_name: string;
  customer_phone: string;
  customer_email: string;
  customer_tax_id?: string;
  customer_person_type?: "individual" | "empresa";
  customer_iva_condition?:
    | "consumidor_final"
    | "responsable_inscripto"
    | "monotributista"
    | "exento";
  delivery_type: "delivery" | "pickup";
  delivery_address: string;
  delivery_city: string;
  delivery_reference: string;
  client_branch_id?: number | null;
  document_type: "sales_invoice" | "sales_quote";
};

function readStorage(): Partial<StoredCheckoutData> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Partial<StoredCheckoutData>;
  } catch {
    return {};
  }
}

function writeStorage(data: Partial<StoredCheckoutData>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    
  }
}

export function useCheckoutStorage() {
  const [savedData, setSavedData] = useState<Partial<StoredCheckoutData> | null>(null);

  useEffect(() => {
    setSavedData(readStorage());
  }, []);

  const saveData = useCallback((data: Partial<StoredCheckoutData>) => {
    const { ...toSave } = data;
    writeStorage(toSave);
  }, []);

  const clearData = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
    setSavedData({});
  }, []);

  return { savedData, saveData, clearData };
}