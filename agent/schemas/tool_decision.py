from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator


class ToolDecision(BaseModel):
    need_tool: bool = Field(default=False)
    tool: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    answer: str = ""

    @model_validator(mode="after")
    def validate_tool_requirements(self):
        if self.need_tool and not self.tool:
            raise ValueError("tool is required when need_tool is true")
        return self
