"use client";

import { useMutation } from "@tanstack/react-query";
import { getAiSuggestionsApi } from "@/features/admin/ai/apis/ai-api";
import type { AiSuggestionsRequest } from "@/features/admin/ai/schemas/ai-schema";

export function useAiSuggestions() {
  return useMutation({
    mutationFn: (data: AiSuggestionsRequest) => getAiSuggestionsApi(data),
  });
}