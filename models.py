from datetime import datetime
import json

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    notes = db.relationship("Note", backref="author", lazy=True, cascade="all, delete")
    files = db.relationship(
        "UploadedFile", backref="owner", lazy=True, cascade="all, delete"
    )
    comments = db.relationship(
        "Comment", backref="author", lazy=True, cascade="all, delete"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Note(TimestampMixin, db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="general")
    post_type = db.Column(db.String(20), nullable=False, default="regular")
    poll_type = db.Column(db.String(20), nullable=True)
    poll_options = db.Column(db.Text, nullable=True)
    quiz_correct_option = db.Column(db.String(255), nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comments = db.relationship("Comment", backref="note", lazy=True, cascade="all, delete")
    votes = db.relationship("PostVote", backref="post", lazy=True, cascade="all, delete")
    poll_responses = db.relationship(
        "PollResponse", backref="post", lazy=True, cascade="all, delete"
    )

    @property
    def rating(self) -> int:
        return sum(v.value for v in self.votes)

    @property
    def poll_options_list(self) -> list[str]:
        if not self.poll_options:
            return []
        try:
            values = json.loads(self.poll_options)
            if isinstance(values, list):
                return [str(item) for item in values]
        except json.JSONDecodeError:
            return []
        return []

    def to_dict(self) -> dict:
        options = []
        if self.poll_options:
            try:
                options = json.loads(self.poll_options)
            except json.JSONDecodeError:
                options = []
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "post_type": self.post_type,
            "poll_type": self.poll_type,
            "poll_options": options,
            "quiz_correct_option": self.quiz_correct_option,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
            "author": self.author.username,
            "rating": self.rating,
        }

    def poll_result_counts(self) -> dict[str, int]:
        counts = {option: 0 for option in self.poll_options_list}
        for response in self.poll_responses:
            if response.selected_option in counts:
                counts[response.selected_option] += 1
        return counts


class Comment(TimestampMixin, db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "body": self.body,
            "author": self.author.username,
            "note_id": self.note_id,
            "created_at": self.created_at.isoformat(),
        }


class PostVote(TimestampMixin, db.Model):
    __tablename__ = "post_votes"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)  # 1 or -1
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "post_id", name="uq_user_post_vote"),)


class PollResponse(TimestampMixin, db.Model):
    __tablename__ = "poll_responses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=False)
    selected_option = db.Column(db.String(255), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "post_id", name="uq_user_post_poll_response"),
    )


class UploadedFile(TimestampMixin, db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original_name": self.original_name,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.created_at.isoformat(),
        }
