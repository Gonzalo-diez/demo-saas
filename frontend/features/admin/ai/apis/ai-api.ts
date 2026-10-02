import { apiFetch } from "@/lib/fetcher";
import {
  aiSuggestionsRequestSchema,
  aiSuggestionsResponseSchema,
  type AiSuggestionsRequest,
  type AiSuggestionsResponse,
} from "@/features/admin/ai/schemas/ai-schema";

export async function getAiSuggestionsApi(
  data: AiSuggestionsRequest
): Promise<AiSuggestionsResponse> {
  const parsedBody = aiSuggestionsRequestSchema.parse(data);

  const response = await apiFetch<unknown>("/api/ai/suggestions", {
    method: "POST",
    body: JSON.stringify(parsedBody),
  });

  return aiSuggestionsResponseSchema.parse(response);
}