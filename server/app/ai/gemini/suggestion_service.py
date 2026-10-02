import json
import re
import time
from typing import Any
from google.genai import errors as genai_errors
from google.genai import types
from sqlalchemy.orm import Session
from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.utils.logging_utils import get_ai_logger
from app.ai.prompts.suggestion_prompt import SUGGESTION_SYSTEM_PROMPT
from app.ai.tools.registry import (
    detect_fallback_tool,
    execute_tool,
    list_tools,
    validate_tool_params,
)
from app.core.config import settings

class GeminiSuggestionService:
    _CACHE: dict[str, dict[str, Any]] = {}
    _CACHE_TTL_SECONDS = 300  # 5 min

    def __init__(self, db: Session):
        self.client = get_gemini_client()
        self.model_name = settings.GEMINI_MODEL
        self.db = db
        self.logger = get_ai_logger()

    def _clean_json_response(self, text: str) -> str:
        return re.sub(r"```json|```", "", text).strip()

    def _normalize_question(self, question: str) -> str:
        return re.sub(r"\s+", " ", question.strip().lower())

    def _get_cache_key(self, question: str) -> str:
        return self._normalize_question(question)

    def _get_cached_response(self, question: str) -> dict[str, Any] | None:
        key = self._get_cache_key(question)
        cached = self._CACHE.get(key)

        if not cached:
            return None

        expires_at = cached["expires_at"]
        if time.time() > expires_at:
            self._CACHE.pop(key, None)
            return None

        return cached["value"]

    def _set_cached_response(self, question: str, value: dict[str, Any]) -> None:
        key = self._get_cache_key(question)
        self._CACHE[key] = {
            "value": value,
            "expires_at": time.time() + self._CACHE_TTL_SECONDS,
        }

    def _error_response(self, reason: str) -> dict:
        return {
            "summary": "No se pudieron generar sugerencias.",
            "suggestions": [
                {
                    "title": "Error de servicio",
                    "reason": reason,
                    "priority": "low",
                }
            ],
        }

    def _build_tool_selector_prompt(self, question: str) -> str:
        tools = list_tools()

        available_tools = []
        for tool in tools:
            available_tools.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "params_schema": tool["params_schema"],
                }
            )

        return f"""
Analiza la pregunta del usuario y elige la herramienta más útil.

REGLAS:
- Responde SOLO en JSON válido.
- Elige UNA sola tool.
- Si ninguna tool aplica claramente, usa una tool general coherente con la pregunta.
- No inventes nombres de tools.
- Usa parámetros simples y válidos según el params_schema.
- Si una tool no necesita parámetros, usa {{}}.
- Si el usuario pregunta por órdenes pendientes, usa get_pending_orders.
- Si el usuario pregunta por clientes sin vendedor, usa get_clients_without_sales_rep.
- Si el usuario pregunta por productos o catálogo en general, usa get_product_catalog_overview.
- Si el usuario pregunta por vendedores, desempeño comercial o equipo de ventas, usa get_sales_rep_performance.
- Si el usuario pregunta por sucursales sin pedidos, usa get_branches_without_orders.
- Si el usuario pregunta por clientes o sucursales con coordenadas, usa get_clients_with_coordinates.
- Si el usuario pregunta por cobertura geográfica, mapa o ubicaciones, prioriza tools basadas en sucursales.
- Si el usuario pregunta por proveedores o lista de proveedores, usa get_suppliers.
- Si el usuario pide un resumen de proveedores, usa get_supplier_overview.
- Si el usuario pregunta por ventas recientes, remitos de venta o últimas ventas, usa get_recent_sales_invoices.
- Si el usuario pregunta por total de ventas, facturación o métricas de ventas, usa get_sales_invoice_overview.
- Si el usuario pregunta por compras, remitos de compra o últimas compras, usa get_recent_purchase_invoices.
- Si el usuario pregunta por total de compras o métricas de compras, usa get_purchase_invoice_overview.
- Si el usuario pregunta por movimientos de stock, entradas o salidas de inventario, usa get_recent_inventory_movements.
- Si el usuario pide un resumen de movimientos de inventario, usa get_inventory_movement_overview.

TOOLS DISPONIBLES:
{json.dumps(available_tools, ensure_ascii=False)}

FORMATO OBLIGATORIO:
{{
  "tool_name": "nombre_tool",
  "params": {{}}
}}

PREGUNTA DEL USUARIO:
{question}
""".strip()

    def _select_tool_without_ai(self, question: str) -> tuple[str, dict[str, Any]]:
        fallback_tool = detect_fallback_tool(question) or "get_dashboard_summary"
        return fallback_tool, {}

    def _select_tool(self, question: str) -> tuple[str, dict[str, Any]]:
        selector_prompt = self._build_tool_selector_prompt(question)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=selector_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        text = response.text or ""
        clean_text = self._clean_json_response(text)
        data = json.loads(clean_text)

        tool_name = data.get("tool_name") or "get_dashboard_summary"
        params = data.get("params") or {}

        if not isinstance(params, dict):
            params = {}

        available_names = {tool["name"] for tool in list_tools()}
        if tool_name not in available_names:
            return self._select_tool_without_ai(question)

        try:
            validated_params = validate_tool_params(tool_name, params)
        except (TypeError, ValueError):
            validated_params = {}

        return tool_name, validated_params

    def _build_analysis_content(
        self,
        question: str,
        selected_tool_name: str,
        selected_tool_params: dict[str, Any],
        tool_result: Any,
    ) -> str:
        payload = {
            "selected_tool": selected_tool_name,
            "tool_params": selected_tool_params,
            "tool_result": tool_result,
            "user_question": question,
        }

        return (
            "DATOS DEL NEGOCIO Y CONTEXTO:\n"
            f"{json.dumps(payload, ensure_ascii=False, default=str)}"
        )

    def _build_direct_fallback_response(
        self,
        question: str,
        tool_name: str,
        tool_result: Any,
    ) -> dict:
        fallback_summaries = {
            "get_pending_orders": "Mostrando estado directo de órdenes pendientes sin usar IA.",
            "get_clients_without_sales_rep": "Mostrando clientes sin vendedor asignado sin usar IA.",
            "get_product_catalog_overview": "Mostrando resumen directo del catálogo sin usar IA.",
            "get_sales_rep_performance": "Mostrando desempeño comercial directo sin usar IA.",
            "get_order_overview": "Mostrando resumen directo de órdenes sin usar IA.",
            "get_client_overview": "Mostrando resumen directo de clientes sin usar IA.",
            "get_dashboard_summary": "Mostrando resumen general directo del negocio sin usar IA.",
        }

        summary = fallback_summaries.get(
            tool_name,
            "No se pudo usar IA. Mostrando datos directos de la herramienta seleccionada.",
        )

        return {
            "summary": summary,
            "suggestions": [],
            "tool_used": tool_name,
            "tool_result": tool_result,
            "fallback_mode": True,
            "question": question,
        }

    def _log_event(
        self,
        *,
        event: str,
        question: str,
        tool_name: str | None = None,
        params: dict[str, Any] | None = None,
        mode: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "event": event,
            "question": question,
            "tool_name": tool_name,
            "params": params or {},
            "mode": mode,
            "extra": extra or {},
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False, default=str))

    def get_suggestions(self, question: str) -> dict:
        cached = self._get_cached_response(question)
        if cached is not None:
            self._log_event(
                event="cache_hit",
                question=question,
                tool_name=cached.get("tool_used"),
                mode="cache",
            )
            return cached

        try:
            tool_name, params = self._select_tool(question)

            self._log_event(
                event="tool_selected",
                question=question,
                tool_name=tool_name,
                params=params,
                mode="ai_selector",
            )

            tool_result = execute_tool(tool_name, self.db, **params)

            self._log_event(
                event="tool_executed",
                question=question,
                tool_name=tool_name,
                params=params,
                mode="ai_selector",
                extra={
                    "result_type": type(tool_result).__name__,
                },
            )

            user_content = self._build_analysis_content(
                question=question,
                selected_tool_name=tool_name,
                selected_tool_params=params,
                tool_result=tool_result,
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=SUGGESTION_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            text = response.text or ""
            clean_text = self._clean_json_response(text)
            parsed = json.loads(clean_text)

            if "tool_used" not in parsed:
                parsed["tool_used"] = tool_name
            parsed["fallback_mode"] = False

            self._set_cached_response(question, parsed)

            self._log_event(
                event="response_generated",
                question=question,
                tool_name=tool_name,
                params=params,
                mode="ai_full",
            )

            return parsed

        except (genai_errors.ClientError, genai_errors.ServerError, json.JSONDecodeError) as e:
            tool_name, params = self._select_tool_without_ai(question)
            tool_result = execute_tool(tool_name, self.db, **params)

            fallback_response = self._build_direct_fallback_response(
                question=question,
                tool_name=tool_name,
                tool_result=tool_result,
            )
            self._set_cached_response(question, fallback_response)

            self._log_event(
                event="fallback_response",
                question=question,
                tool_name=tool_name,
                params=params,
                mode="fallback",
                extra={"error": str(e)},
            )

            return fallback_response

        except KeyError as e:
            self._log_event(
                event="error",
                question=question,
                mode="error",
                extra={"error": f"Tool no registrada: {str(e)}"},
            )
            return self._error_response(f"Tool no registrada: {str(e)}")

        except TypeError as e:
            self._log_event(
                event="error",
                question=question,
                mode="error",
                extra={"error": f"Parámetros inválidos para la tool: {str(e)}"},
            )
            return self._error_response(f"Parámetros inválidos para la tool: {str(e)}")

        except Exception as e:
            self._log_event(
                event="error",
                question=question,
                mode="error",
                extra={"error": str(e)},
            )
            return self._error_response(f"Error interno al procesar la sugerencia: {str(e)}")