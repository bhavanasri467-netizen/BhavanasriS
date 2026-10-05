# ComicCraft — AI Comic Story Creator

ComicCraft is a FastAPI + Jinja2 web application that turns a user's story idea into a five-panel comic. It follows the architecture in the supplied project specification:

1. Gemini Flash generates a structured five-panel outline.
2. Gemini Pro expands the outline into narration and dialogue.
3. A text-to-image model creates one illustration per panel.
4. The layout builder joins the images and story text.
5. FPDF2 exports the result as a downloadable PDF.

## Compatibility update

The original project document names Gemini 1.5 models and the legacy `google-generativeai` package. This implementation uses Google's current `google-genai` SDK and configurable Gemini model names. The image layer uses Hugging Face `InferenceClient` by default because it avoids requiring a local GPU. A local Diffusers backend is also included as an optional backend.

## Project structure

```text
comiccraft/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   └── services/
│       ├── __init__.py
│       ├── gemini_flash.py
│       ├── gemini_pro.py
│       ├── image_generator.py
│       ├── layout_builder.py
│       └── exporters.py
├── static/
│   ├── css/style.css
│   ├── panels/.gitkeep
│   └── exports/.gitkeep
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── comic_preview.html
│   ├── export_success.html
│   └── error.html
├── tests/test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── requirements-local-diffusion.txt
```

## 1. VS Code setup

Install Python 3.11 or newer, VS Code, and the Python extension.

Open the `comiccraft` folder in VS Code.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## 2. Configure AI keys

Open `.env`.

For real story generation, set:

```env
GEMINI_API_KEY=your_key_here
```

For real image generation with Hugging Face, also set:

```env
HF_TOKEN=your_token_here
IMAGE_GENERATION_MODE=hf
```

The Hugging Face token must have permission to use Inference Providers. The application uses automatic provider selection.

## 3. Run without any API key first

For a guaranteed local smoke test, set:

```env
DEMO_MODE=true
IMAGE_GENERATION_MODE=demo
```

Then run:

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

Demo mode creates a complete comic using deterministic placeholder artwork, so you can verify the frontend, routes, layout, and PDF export before configuring external AI services.

## 4. Run with real AI

Set:

```env
DEMO_MODE=false
IMAGE_GENERATION_MODE=hf
GEMINI_API_KEY=...
HF_TOKEN=...
```

Then:

```bash
uvicorn app.main:app --reload
```

Open:

- Home: http://127.0.0.1:8000
- Swagger API docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 5. Optional local Stable Diffusion backend

If you have a suitable PyTorch environment and want generation on your own machine:

```bash
pip install -r requirements-local-diffusion.txt
```

Then configure:

```env
IMAGE_GENERATION_MODE=local
LOCAL_IMAGE_MODEL=runwayml/stable-diffusion-v1-5
```

The first local generation downloads the model and can require several GB of storage and substantial RAM/VRAM. The Hugging Face backend is recommended for ordinary laptops.

## 6. Test the API

With the server running, open `/docs` and try `POST /generate-comic/json` with:

```json
{
  "story_prompt": "A brave fox explores an enchanted forest and discovers a lost magical seed.",
  "character_name": "Lumi",
  "setting": "enchanted forest",
  "tone": "funny",
  "art_style": "comic book"
}
```

A successful response contains a `comic_id`, five-panel `layout`, and a `pdf_url`.

## 7. Automated tests

With the virtual environment activated:

```bash
pytest -q
```

The tests use demo mode and do not call Gemini or Hugging Face.

## 8. Important implementation details

- Generated files are stored under `static/panels` and `static/exports`.
- Comic records are stored in memory for this local project. Restarting the server clears the in-memory records.
- `/generate` is the browser form workflow.
- `/generate-comic/json` is the JSON API workflow.
- `/test-image` tests image generation independently.
- `/export/{comic_id}` creates/returns the PDF.
- `/export-success` renders the final confirmation page.

## 9. Troubleshooting

### `GEMINI_API_KEY is not configured`
Use `DEMO_MODE=true` for testing, or put a valid Gemini API key in `.env` and restart Uvicorn.

### Hugging Face image generation fails
Check `HF_TOKEN`, the selected model, and your Hugging Face Inference Provider access. You can temporarily set `IMAGE_GENERATION_MODE=demo` to test the rest of the application.

### Local Diffusers is slow or out of memory
Use `IMAGE_GENERATION_MODE=hf` instead. Local diffusion is intentionally optional.

### PDF cannot be opened
Make sure the generated image files exist and rerun the export. The exporter validates every panel image before writing the PDF.
