from pathlib import Path

from flask import Flask
from sqlalchemy import inspect, text

from config import Config
from extensions import db, login_manager
from routes.api import api_bp
from routes.auth import auth_bp
from routes.main import main_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        from models import Comment, Note, PollResponse, PostVote, UploadedFile, User  # noqa: F401

        db.create_all()
        ensure_schema_updates()

    return app


def ensure_schema_updates():
    """Lightweight runtime migrations for SQLite учебного проекта."""
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    if "notes" in tables:
        note_columns = {col["name"] for col in inspector.get_columns("notes")}
        if "post_type" not in note_columns:
            db.session.execute(
                text("ALTER TABLE notes ADD COLUMN post_type VARCHAR(20) NOT NULL DEFAULT 'regular'")
            )
        if "poll_type" not in note_columns:
            db.session.execute(text("ALTER TABLE notes ADD COLUMN poll_type VARCHAR(20)"))
        if "poll_options" not in note_columns:
            db.session.execute(text("ALTER TABLE notes ADD COLUMN poll_options TEXT"))
        if "quiz_correct_option" not in note_columns:
            db.session.execute(text("ALTER TABLE notes ADD COLUMN quiz_correct_option VARCHAR(255)"))
        db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
