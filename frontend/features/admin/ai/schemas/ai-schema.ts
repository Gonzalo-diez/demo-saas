import { z } from "zod";

export const aiSuggestionPrioritySchema = z.enum(["high", "medium", "low"]);

export const aiSuggestionItemSchema = z.object({
  title: z.string().min(1, "El título es obligatorio"),
  reason: z.string().min(1, "La razón es obligatoria"),
  priority: aiSuggestionPrioritySchema,
});

export const aiSuggestionsRequestSchema = z.object({
  question: z
    .string()
    .min(3, "La pregunta debe tener al menos 3 caracteres")
    .max(1000, "La pregunta no puede superar los 1000 caracteres"),
});

export const aiSuggestionsResponseSchema = z.object({
  summary: z.string(),
  suggestions: z.array(aiSuggestionItemSchema),
  tool_used: z.string().optional(),
  fallback_mode: z.boolean().optional(),
  tool_result: z.unknown().optional(),
  question: z.string().optional(),
});

export type AiSuggestionPriority = z.infer<typeof aiSuggestionPrioritySchema>;
export type AiSuggestionItem = z.infer<typeof aiSuggestionItemSchema>;
export type AiSuggestionsRequest = z.infer<typeof aiSuggestionsRequestSchema>;
export type AiSuggestionsResponse = z.infer<typeof aiSuggestionsResponseSchema>;