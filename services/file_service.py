import os
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename


def is_allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def ensure_upload_folder() -> None:
    Path(current_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)


def save_uploaded_file(file_storage) -> tuple[str, str]:
    ensure_upload_folder()
    original_name = secure_filename(file_storage.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    target = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(target)
    return original_name, unique_name

