import os
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import settings

UPLOAD_DIR = Path(settings.upload_dir)


async def save_upload(file: UploadFile, agency_id: str, creator_id: str) -> str:
    directory = UPLOAD_DIR / "media-kits" / agency_id / creator_id
    directory.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "media-kit.pdf"
    safe_filename = filename.replace(os.sep, "_")
    filepath = directory / safe_filename

    contents = await file.read()
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)

    return str(filepath.relative_to(UPLOAD_DIR.parent))
