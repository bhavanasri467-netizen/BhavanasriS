from __future__ import annotations

from google import genai
from google.genai import types

from app.config import DEMO_MODE, GEMINI_API_KEY, GEMINI_FLASH_MODEL
from app.models import ComicOutline, ComicStory, PanelStory, PromptRequest


def _demo_story(request: PromptRequest, outline: ComicOutline) -> ComicStory:
    return ComicStory(panels=[
        PanelStory(
            panel_number=1,
            caption="The wind rustles through the trees.",
            narration=f"{request.character_name} steps into the {request.setting}, ready for an adventure.",
            dialogue=f'"I have a feeling something amazing is waiting here," says {request.character_name}.'
        ),
        PanelStory(
            panel_number=2,
            caption="A tiny magical glow flickers nearby.",
            narration=f"A strange discovery catches {request.character_name}'s attention and turns curiosity into excitement.",
            dialogue='"Whoa! That definitely was not here a moment ago!"'
        ),
        PanelStory(
            panel_number=3,
            caption="CRASH! The peaceful moment is over.",
            narration="The unexpected obstacle blocks the path, and the hero has only seconds to react.",
            dialogue='"Okay... new plan. Stay calm!"'
        ),
        PanelStory(
            panel_number=4,
            caption="WHOOSH! Courage takes over.",
            narration=f"With quick thinking, {request.character_name} finds a clever way around the danger.",
            dialogue='"Sometimes the strangest problems need the strangest ideas!"'
        ),
        PanelStory(
            panel_number=5,
            caption="The adventure ends beneath a glowing sky.",
            narration=f"{request.character_name} looks back at the {request.setting}, smiling at everything that happened and wondering what tomorrow will bring.",
            dialogue='"I think this is only the beginning."'
        ),
    ])


def generate_story(request: PromptRequest, outline: ComicOutline) -> ComicStory:
    if DEMO_MODE:
        return _demo_story(request, outline)

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Set it in .env or enable DEMO_MODE."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    outline_text = outline.model_dump_json(indent=2)

    prompt = f"""
Expand this five-panel comic outline into polished comic narration and dialogue.

Character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}
Original prompt: {request.story_prompt}

Outline:
{outline_text}

Requirements:
- Return exactly five panels in the same order.
- Keep continuity between panels.
- caption is short ambient/action text, like a comic caption or sound effect.
- narration is concise but vivid.
- dialogue should sound natural and match the requested tone.
- Do not invent additional named main characters unless needed by the story.
"""

    # Use the same working Gemini Flash model instead of Gemini Pro.
    response = client.models.generate_content(
        model=GEMINI_FLASH_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,
            response_mime_type="application/json",
            response_schema=ComicStory,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return ComicStory.model_validate_json(response.text)