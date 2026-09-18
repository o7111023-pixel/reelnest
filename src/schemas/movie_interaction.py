from pydantic import BaseModel


class InteractionResponse(BaseModel):
    message: str
