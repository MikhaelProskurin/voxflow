import os
from io import BytesIO

from typing import Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.exceptions import OutputParserException

from .prompts import (
    AGENT_ROLE_PROMPT,
    TASK_EXTRACTION_REQUEST_PROMPT,
)

class VoxFlowAgentConfig(BaseModel):
    openai_api_key: str
    openrouter_api_key: str
    model_name: str
    transcription_model_name: str = "whisper-1"
    base_url: Optional[str]
    temperature: Optional[float] = 0.0
    fallback_temperature: Optional[float] = 0.3


class TaskModel(BaseModel):
    title: str = Field(description="Short, action-oriented task title (e.g. 'Call dentist', 'Submit report'). No filler words.")
    description: str = Field(description="Any additional detail from the input that did not fit in the title. Empty string if none.")
    due_date: str = Field(description="Due date exactly as expressed in the input (e.g. 'tomorrow', 'next Monday at 3pm', 'in two hours'). Empty string if not mentioned.")


class ExtractedTasksModel(BaseModel):
    content: list[TaskModel] = Field(description="All tasks extracted from the input. One entry per distinct task.")


class VoxflowAgent:

    def __init__(self, config: VoxFlowAgentConfig) -> None:
        self.config = config
        self.openai_compatible_client = ChatOpenAI(
            api_key=config.openrouter_api_key if config.openrouter_api_key else config.openai_api_key,
            model=config.model_name,
            base_url=config.base_url if config.openrouter_api_key else None,
            temperature=config.temperature,
        )
        self.fallback_client = self.openai_compatible_client.with_config(
            RunnableConfig(configurable={"temperature": config.fallback_temperature})
        )
        self.openai_whisper_client = AsyncOpenAI(api_key=config.openai_api_key)
    
    async def transcribe(self, audio_data: bytes) -> str:
        buffer = BytesIO(audio_data)
        buffer.name = "voice.ogg"

        response = await self.openai_whisper_client.audio.transcriptions.create(
            file=buffer,
            model=self.config.transcription_model_name,
            temperature=self.config.temperature
        )
        return response.text
    
    async def extract_tasks_from_text(self, text: str, n_retries: int = 3) -> ExtractedTasksModel:
        
        parser = PydanticOutputParser(pydantic_object=ExtractedTasksModel)

        prompt = [
            SystemMessage(content=AGENT_ROLE_PROMPT.format(fmt=parser.get_format_instructions())),
            HumanMessage(content=TASK_EXTRACTION_REQUEST_PROMPT.format(text=text))
        ]

        response: AIMessage = await self.openai_compatible_client.ainvoke(prompt)
        for retry in range(n_retries):
            try:
                content = parser.parse(response.text)
                return content
            except OutputParserException:
                response = await self.fallback_client.ainvoke(prompt)
        else:
            raise RuntimeError("Failed to extract the tasks from input!")


def create_voxflow_agent() -> VoxflowAgent:
    return VoxflowAgent(
            VoxFlowAgentConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            model_name=os.getenv("MODEL_NAME"),
            base_url=os.getenv("BASE_URL"),
            transcription_model_name=os.getenv("TRANSCRIPTION_MODEL_NAME"),
            temperature=os.getenv("TEMPERATURE"),
            fallback_temperature=os.getenv("FALLBACK_TEMPERATURE"),
        )
    )
