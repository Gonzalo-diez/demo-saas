from pydantic import BaseModel
from typing import List, Literal

class AiSuggestionsRequest(BaseModel):
    question: str

class SuggestionItem(BaseModel):
    title: str
    reason: str
    priority: Literal["high", "medium", "low"]

class AiSuggestionsResponse(BaseModel):
    summary: str
    suggestions: List[SuggestionItem]