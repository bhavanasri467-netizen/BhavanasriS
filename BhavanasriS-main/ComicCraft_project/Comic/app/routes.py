from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.models import PromptRequest
from app.services.exporters import save_pdf
from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

COMICS: dict[str, dict] = {}


def _create_comic(request_data: PromptRequest) -> tuple[str, dict]:
    outline = generate_outline(request_data)
    story = generate_story(request_data, outline)
    image_paths = [generate_image(panel.image_prompt, panel.panel_number) for panel in outline.panels]
    layout = build_comic_layout(outline, story, image_paths)
    comic_id = uuid4().hex
    comic = {
        "id": comic_id,
        "request": request_data.model_dump(),
        "layout": layout,
        "pdf_url": None,
    }
    COMICS[comic_id] = comic
    return comic_id, comic


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"title": "ComicCraft"})


@router.post("/generate", response_class=HTMLResponse)
async def generate_form(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        data = PromptRequest(story_prompt=story_prompt, character_name=character_name, setting=setting, tone=tone, art_style=art_style)
        comic_id, comic = _create_comic(data)
        return templates.TemplateResponse(request=request, name="comic_preview.html", context={"title": "Comic Preview", "comic": comic, "comic_id": comic_id})
    except Exception as exc:
        logger.exception("Comic generation failed")
        return templates.TemplateResponse(request=request, name="error.html", context={"title": "Generation Error", "error": str(exc)}, status_code=500)


@router.post("/generate-comic/json")
async def generate_json(data: PromptRequest):
    try:
        comic_id, comic = _create_comic(data)
        return JSONResponse({"success": True, "comic_id": comic_id, "layout": comic["layout"], "pdf_url": f"/export/{comic_id}"})
    except Exception as exc:
        logger.exception("JSON comic generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/export/{comic_id}")
async def export_comic(comic_id: str):
    comic = COMICS.get(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found. Generate a new comic first.")
    if not comic["pdf_url"]:
        comic["pdf_url"] = save_pdf(comic["layout"])
    return RedirectResponse(url=f"/export-success?pdf_url={comic['pdf_url']}", status_code=303)


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_url: str):
    if not pdf_url.startswith("/static/exports/"):
        raise HTTPException(status_code=400, detail="Invalid PDF path.")
    return templates.TemplateResponse(request=request, name="export_success.html", context={"title": "Export Complete", "pdf_url": pdf_url})


@router.get("/test-image")
async def test_image(prompt: str = "A friendly fox in an enchanted forest, colorful comic book art"):
    try:
        path = generate_image(prompt, 999)
        return {"success": True, "image_url": path, "prompt": prompt}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
