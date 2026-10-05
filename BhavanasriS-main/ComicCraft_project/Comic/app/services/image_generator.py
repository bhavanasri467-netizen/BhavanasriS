from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import HF_IMAGE_MODEL, HF_TOKEN, LOCAL_IMAGE_MODEL, PANELS_DIR, IMAGE_GENERATION_MODE


def _safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")
    return value[:80] or "panel"


def _font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _demo_image(prompt: str, panel_number: int, path: Path) -> None:
    image = Image.new("RGB", (1024, 768), "#f3eadb")
    draw = ImageDraw.Draw(image)
    draw.rectangle((25, 25, 999, 743), outline="#222222", width=8)
    draw.rectangle((55, 55, 969, 135), fill="#222222")
    draw.text((80, 77), f"COMICCRAFT • PANEL {panel_number}", fill="white", font=_font(36))
    wrapped = prompt[:360]
    words = wrapped.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 > 42:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    y = 220
    for line in lines[:8]:
        draw.text((90, y), line, fill="#222222", font=_font(28))
        y += 48
    draw.ellipse((760, 545, 920, 705), outline="#222222", width=8)
    draw.text((785, 595), "AI", fill="#222222", font=_font(50))
    image.save(path, format="PNG")


def _hf_image(prompt: str, path: Path) -> None:
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is not configured for Hugging Face image generation.")
    from huggingface_hub import InferenceClient

    client = InferenceClient(api_key=HF_TOKEN)
    image = client.text_to_image(prompt=prompt, model=HF_IMAGE_MODEL)
    image.save(path)


def _local_image(prompt: str, path: Path) -> None:
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError as exc:
        raise RuntimeError("Local image mode requires requirements-local-diffusion.txt") from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(LOCAL_IMAGE_MODEL, torch_dtype=dtype)
    pipe = pipe.to(device)
    image = pipe(prompt, num_inference_steps=20, guidance_scale=7.0).images[0]
    image.save(path)


def generate_image(prompt: str, panel_number: int) -> str:
    print("IMAGE MODE:", IMAGE_GENERATION_MODE)
    filename = f"panel_{panel_number}_{_safe_name(prompt)[:40]}.png"
    path = PANELS_DIR / filename
    if IMAGE_GENERATION_MODE == "demo":
        _demo_image(prompt, panel_number, path)
    elif IMAGE_GENERATION_MODE == "hf":
        _hf_image(prompt, path)
    elif IMAGE_GENERATION_MODE == "local":
        _local_image(prompt, path)
    else:
        raise RuntimeError(f"Unknown IMAGE_GENERATION_MODE: {IMAGE_GENERATION_MODE}")
    return f"/static/panels/{filename}"
