# /// script
# requires-python = ">=3.12"
# dependencies = ["fastapi", "marimo", "starlette", "requests", "pydantic", "jinja2"]
# ///
import os
import tempfile
from pathlib import Path

import marimo
import requests
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

GITHUB_REPO = os.environ.get("GITHUB_REPO", "marimo-team/marimo")
ROOT_DIR = os.environ.get("GITHUB_ROOT_DIR", "examples/ui")


def download_github_files(repo: str, path: str = "") -> list[tuple[str, str]]:
    """Download files from GitHub repo, returns list of (file_path, content)"""
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    response = requests.get(api_url)
    response.raise_for_status()

    files: list[tuple[str, str]] = []
    for item in response.json():
        if item["type"] == "file" and item["name"].endswith(".py"):
            content_response = requests.get(item["download_url"])
            files.append((Path(path) / item["name"], content_response.text))
        elif item["type"] == "dir":
            files.extend(download_github_files(repo, str(Path(path) / item["name"])))
    return files


files = download_github_files(GITHUB_REPO, ROOT_DIR)

server = marimo.create_asgi_app()
tmp_dir = tempfile.TemporaryDirectory()
app_names: list[str] = []

for file_path, content in files:
    app_name = Path(file_path).stem
    local_path = Path(tmp_dir.name) / file_path

    # Create directories if they don't exist
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file content
    local_path.write_text(content)

    # Add to marimo server
    print(f"Adding app: {app_name}")
    server = server.with_app(path=f"/{app_name}", root=str(local_path))
    app_names.append(app_name)


app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html", {"request": request, "app_names": app_names}
    )


# Mount the marimo server
app.mount("/", server.build())

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
