from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CVTextInput(BaseModel):
    instruction: str = Field(
        default="Read the CV text provided by the user.",
        description="Instruction for reviewing the extracted CV text.",
    )


class CVTextTool(BaseTool):
    name: str = "CV text reader"
    description: str = (
        "Read text already extracted from the user's PDF or DOCX CV. "
        "The original file is not saved by this tool."
    )
    args_schema: type[BaseModel] = CVTextInput
    cv_text: str

    def _run(self, instruction: str = "Read the CV text.") -> str:
        if not self.cv_text.strip():
            return "No readable CV text was provided."
        return self.cv_text[:24000]
