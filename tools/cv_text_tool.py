from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CVTextInput(BaseModel):
    instruction: str = Field(
        default="Review the CV description pasted by the user.",
        description="Instruction for reviewing the candidate's CV description.",
    )


class CVTextTool(BaseTool):
    name: str = "CV description reader"
    description: str = (
        "Read the CV description pasted by the user. Extract only information "
        "that appears in that description."
    )
    args_schema: type[BaseModel] = CVTextInput
    cv_text: str

    def _run(
        self,
        instruction: str = "Review the CV description pasted by the user.",
    ) -> str:
        if not self.cv_text.strip():
            return "The user has not provided CV text."
        return self.cv_text[:10000]
