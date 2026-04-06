from typing import TypeVar

from google import genai
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)

client = genai.Client(api_key=settings.gemini_api_key)

FAST_MODEL = "gemini-2.5-flash"
QUALITY_MODEL = "gemini-2.5-pro"


async def generate_structured(
    prompt: str,
    output_schema: type[T],
    model: str = FAST_MODEL,
    system_instruction: str | None = None,
) -> T:
    """Call Gemini and get a response that conforms to the given Pydantic schema."""
    config: dict = {
        "response_mime_type": "application/json",
        "response_schema": output_schema,
    }
    if system_instruction:
        config["system_instruction"] = system_instruction

    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    return output_schema.model_validate_json(response.text)
