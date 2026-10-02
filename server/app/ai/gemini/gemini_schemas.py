from pydantic import BaseModel

class AiTestRequest(BaseModel):
    prompt: str

class AiTestResponse(BaseModel):
    response: str