from __future__ import annotations

from google import genai
from google.genai import types

from app.config import DEMO_MODE, GEMINI_API_KEY, GEMINI_FLASH_MODEL
from app.models import ComicOutline, PanelOutline, PromptRequest


def _demo_outline(request: PromptRequest) -> ComicOutline:
    return ComicOutline(panels=[
        PanelOutline(panel_number=1, title="The Beginning", scene_description=f"{request.character_name} arrives at the {request.setting} with a mysterious plan.", image_prompt=f"{request.character_name} entering a {request.setting}, {request.art_style} comic illustration, cinematic composition"),
        PanelOutline(panel_number=2, title="A Strange Discovery", scene_description=f"Something unexpected appears, changing the direction of the adventure.", image_prompt=f"{request.character_name} discovering something magical in a {request.setting}, {request.art_style} comic illustration"),
        PanelOutline(panel_number=3, title="Trouble Arrives", scene_description="A sudden obstacle forces the hero to make a brave choice.", image_prompt=f"hero facing a dramatic obstacle in a {request.setting}, expressive action, {request.art_style} comic illustration"),
        PanelOutline(panel_number=4, title="The Turning Point", scene_description=f"{request.character_name} uses courage and creativity to overcome the challenge.", image_prompt=f"{request.character_name} overcoming a challenge in a {request.setting}, dynamic heroic pose, {request.art_style} comic illustration"),
        PanelOutline(panel_number=5, title="A New Chapter", scene_description="The adventure ends with a satisfying discovery and a hint of what comes next.", image_prompt=f"{request.character_name} celebrating at the {request.setting}, warm ending, {request.art_style} comic illustration"),
    ])


def generate_outline(request: PromptRequest) -> ComicOutline:
    if DEMO_MODE:
        return _demo_outline(request)
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured. Set it in .env or enable DEMO_MODE.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
Create exactly five connected comic panels for this user idea.

Story prompt: {request.story_prompt}
Main character: {request.character_name}
Setting: {request.setting}
Tone: {request.tone}
Art style: {request.art_style}

Requirements:
- Preserve the user's premise.
- Make the five panels form a clear beginning, development, conflict, turning point, and ending.
- Keep the main character visually consistent.
- scene_description should describe what happens in that panel.
- image_prompt should be a detailed visual prompt and must include the requested art style.
- Do not put dialogue into image_prompt.
"""
    response = client.models.generate_content(
        model=GEMINI_FLASH_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.8,
            response_mime_type="application/json",
            response_schema=ComicOutline,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini Flash returned an empty response.")
    return ComicOutline.model_validate_json(response.text)
