"use client";

import { useState } from "react";
import { Sparkles, Send, RefreshCw, AlertCircle, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useAiSuggestions } from "@/features/admin/ai/hooks/use-ai-suggestions";
import type { AiSuggestionPriority } from "@/features/admin/ai/schemas/ai-schema";
import { cn } from "@/lib/utils";

// 1. Definimos la interfaz para que TypeScript sepa qué contiene 'data'
interface AiSuggestion {
  title: string;
  priority: AiSuggestionPriority;
  reason: string;
}

interface AiResponse {
  summary: string;
  tool_used?: string | null;
  fallback_mode?: boolean;
  suggestions: AiSuggestion[];
}

const EXAMPLE_PROMPTS = [
  "¿Qué debería priorizar hoy para mejorar ventas?",
  "¿Hay clientes sin vendedor asignado?",
  "¿Qué productos tienen stock bajo?",
  "¿Qué sucursales activas todavía no tienen pedidos?",
  "Dame un resumen operativo del negocio.",
];

function getPriorityConfig(priority: AiSuggestionPriority) {
  const configs = {
    high: { label: "Alta", classes: "border-stamp/20 bg-stamp/10 text-stamp" },
    medium: { label: "Media", classes: "border-[var(--kraft)]/20 bg-[var(--kraft)]/10 text-[var(--kraft)]" },
    low: { label: "Baja", classes: "border-border bg-muted text-muted-foreground" },
  };
  return configs[priority] || configs.low;
}

export function AiAssistantCard() {
  const [question, setQuestion] = useState("");
  
  // 2. Tipamos el hook (si tu hook lo permite) o casteamos la data abajo
  const aiMutation = useAiSuggestions();
  
  // Forzamos el tipo aquí para eliminar los errores de "Property does not exist on type {}"
  const data = aiMutation.data as AiResponse | undefined;
  const { isPending, isError, error } = aiMutation;

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isPending) return;
    aiMutation.mutate({ question: trimmed });
  }

  return (
    <section className="rounded-2xl border bg-card p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Bot className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-tight">Asistente IA</h2>
          <p className="text-sm text-muted-foreground italic">Analista experto en operaciones</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Textarea
          placeholder="Ej: ¿Qué clientes no tienen vendedor asignado?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={4}
          className="resize-none focus-visible:ring-primary/30"
        />

        <div className="flex flex-wrap gap-2">
          {EXAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => setQuestion(prompt)}
              className="rounded-full border bg-muted/30 px-3 py-1 text-[11px] font-medium transition hover:bg-primary/10"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="flex justify-end">
          <Button type="submit" disabled={isPending} className="gap-2">
            {isPending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {isPending ? "Analizando..." : "Consultar"}
          </Button>
        </div>
      </form>

      {isError && (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="w-4 h-4" />
          {error instanceof Error ? error.message : "Error al consultar la IA"}
        </div>
      )}

      {/* 3. Renderizado de resultados con tipos validados */}
      {data && (
        <div className="mt-8 space-y-6 animate-in fade-in">
          <div className="rounded-xl border bg-muted/10 p-5">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-primary/80">Resumen</h3>
              {data.tool_used && (
                <Badge variant="outline" className="text-[10px]">{data.tool_used}</Badge>
              )}
            </div>
            <p className="text-sm leading-relaxed">{data.summary}</p>
            {data.fallback_mode && (
              <p className="mt-2 text-xs text-kraft font-medium">⚠️ Modo fallback: Datos sin análisis profundo.</p>
            )}
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-bold">Sugerencias de Acción</h3>
            {data.suggestions.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">No hay sugerencias específicas.</p>
            ) : (
              <div className="grid gap-3">
                {data.suggestions.map((item, index) => {
                  const { label, classes } = getPriorityConfig(item.priority);
                  return (
                    <article key={index} className="rounded-xl border bg-background p-4 shadow-sm">
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <h4 className="font-semibold text-sm">{item.title}</h4>
                        <span className={cn("rounded-full border px-2 py-0.5 text-[10px] font-bold", classes)}>
                          {label}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">{item.reason}</p>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}