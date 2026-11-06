from pydantic import BaseModel, Field
from typing import Any
class ProjectUpdate(BaseModel):
    title: str | None = None
    project: dict[str, Any] | None = None
class RenderRequest(BaseModel):
    project: dict[str, Any] = Field(default_factory=dict)
