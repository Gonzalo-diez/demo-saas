import { API_URL } from "@/lib/api";

type FetchOptions = RequestInit;

export async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const isFormData = options.body instanceof FormData;

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Ocurrió un error";

    try {
      const errorData = await response.json();
      message = errorData.detail ?? message;
    } catch {}

    throw new Error(message);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Variante de apiFetch para endpoints que devuelven un archivo binario
 * (Excel, PDF, etc). Devuelve el Blob listo para descargar.
 */
export async function apiFetchBlob(
  endpoint: string,
  options: FetchOptions = {}
): Promise<Blob> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Ocurrió un error";

    try {
      const errorData = await response.json();
      message = errorData.detail ?? message;
    } catch {}

    throw new Error(message);
  }

  return response.blob();
}

/**
 * Dispara la descarga de un Blob en el navegador con el nombre indicado.
 */
export function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}