import os

os.environ["DEMO_MODE"] = "true"
os.environ["IMAGE_GENERATION_MODE"] = "demo"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "ComicCraft" in response.text


def test_json_generation_and_export():
    payload = {
        "story_prompt": "A brave fox explores an enchanted forest.",
        "character_name": "Lumi",
        "setting": "enchanted forest",
        "tone": "funny",
        "art_style": "comic book",
    }
    response = client.post("/generate-comic/json", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["layout"]) == 5

    export = client.get(data["pdf_url"], follow_redirects=True)
    assert export.status_code == 200
    assert "Export Complete" in export.text
