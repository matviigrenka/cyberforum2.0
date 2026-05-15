import json

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from extensions import db
from models import Comment, Note, PostVote
from services.weather_service import WeatherServiceError, get_weather_for_city


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "forum-flask"}), 200


@api_bp.get("/posts/public")
@api_bp.get("/notes/public")
def public_posts():
    posts = Note.query.filter_by(is_public=True).order_by(Note.created_at.desc()).all()
    return jsonify({"items": [n.to_dict() for n in posts]})


@api_bp.get("/posts/my")
@api_bp.get("/notes/my")
@login_required
def my_posts():
    posts = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return jsonify({"items": [n.to_dict() for n in posts]})


@api_bp.post("/posts")
@api_bp.post("/notes")
@login_required
def create_post():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    category = str(data.get("category", "general")).strip() or "general"
    custom_category = str(data.get("custom_category", "")).strip()
    if custom_category:
        category = custom_category[:50]
    is_public = bool(data.get("is_public", False))
    post_type = str(data.get("post_type", "regular")).strip() or "regular"
    poll_type = str(data.get("poll_type", "")).strip() or None
    if post_type not in {"regular", "voting", "quiz"}:
        return jsonify({"error": "Invalid post_type"}), 400
    if post_type == "voting":
        poll_type = "anonymous"
    elif post_type == "quiz":
        poll_type = "quiz"
    else:
        poll_type = None
    poll_options = None
    quiz_correct_option = None

    if len(title) < 3:
        return jsonify({"error": "Validation error"}), 400
    if post_type in {"voting", "quiz"}:
        raw_options = data.get("poll_options", [])
        if not isinstance(raw_options, list):
            return jsonify({"error": "poll_options must be an array"}), 400
        options = [str(item).strip() for item in raw_options if str(item).strip()]
        if len(options) < 2:
            return jsonify({"error": "Voting post requires at least 2 options"}), 400
        poll_options = json.dumps(options, ensure_ascii=False)
        content = "Quiz post" if post_type == "quiz" else "Voting post"
        if post_type == "quiz":
            quiz_correct_option = str(data.get("quiz_correct_option", "")).strip()
            if quiz_correct_option not in options:
                return jsonify({"error": "quiz_correct_option must match one option"}), 400
    else:
        if len(content) < 10:
            return jsonify({"error": "Validation error"}), 400

    post = Note(
        title=title,
        content=content,
        category=category,
        post_type=post_type,
        poll_type=poll_type,
        poll_options=poll_options,
        quiz_correct_option=quiz_correct_option,
        is_public=is_public,
        user_id=current_user.id,
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({"item": post.to_dict()}), 201


@api_bp.get("/posts/<int:post_id>/comments")
@api_bp.get("/notes/<int:post_id>/comments")
def post_comments(post_id: int):
    post = Note.query.get_or_404(post_id)
    if not post.is_public:
        return jsonify({"error": "Post is private"}), 403
    return jsonify({"items": [c.to_dict() for c in post.comments]})


@api_bp.post("/posts/<int:post_id>/comments")
@api_bp.post("/notes/<int:post_id>/comments")
@login_required
def create_comment(post_id: int):
    post = Note.query.get_or_404(post_id)
    if not post.is_public and post.user_id != current_user.id:
        return jsonify({"error": "No access"}), 403

    data = request.get_json(silent=True) or {}
    body = str(data.get("body", "")).strip()
    if len(body) < 2:
        return jsonify({"error": "Validation error"}), 400

    comment = Comment(body=body, note_id=post.id, user_id=current_user.id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({"item": comment.to_dict()}), 201


@api_bp.post("/posts/<int:post_id>/vote")
@login_required
def vote_post(post_id: int):
    post = Note.query.get_or_404(post_id)
    data = request.get_json(silent=True) or {}
    value = int(data.get("value", 0))
    if value not in {-1, 1}:
        return jsonify({"error": "Value must be 1 or -1"}), 400

    existing = PostVote.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        existing.value = value
    else:
        db.session.add(PostVote(user_id=current_user.id, post_id=post.id, value=value))
    db.session.commit()
    return jsonify({"post_id": post.id, "rating": post.rating})


@api_bp.get("/weather")
def weather():
    city = request.args.get("city", "Vladivostok")
    try:
        snapshot = get_weather_for_city(city)
        return jsonify({"city": city, "weather": snapshot.to_dict()})
    except WeatherServiceError as exc:
        return jsonify({"error": str(exc)}), 400
