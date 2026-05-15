import os
import json

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from extensions import db
from forms import CommentForm, PostForm
from models import Comment, Note, PollResponse, PostVote, UploadedFile
from services.file_service import is_allowed_file, save_uploaded_file


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    public_posts = (
        Note.query.filter_by(is_public=True).order_by(Note.created_at.desc()).limit(9).all()
    )
    return render_template("index.html", public_posts=public_posts)


@main_bp.route("/api-docs")
def api_docs():
    return render_template("api_docs.html")


@main_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = PostForm()
    if form.validate_on_submit():
        custom_category = (form.custom_category.data or "").strip()
        category = form.category.data
        if category == "other":
            if not custom_category:
                flash("Please enter a custom category when 'Other' is selected.", "warning")
                posts = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
                files = (
                    UploadedFile.query.filter_by(user_id=current_user.id)
                    .order_by(UploadedFile.created_at.desc())
                    .all()
                )
                return render_template("dashboard.html", form=form, posts=posts, files=files)
            category = custom_category
        post_type = form.post_type.data
        poll_type = "quiz" if post_type == "quiz" else ("anonymous" if post_type == "voting" else None)
        poll_options = None
        quiz_correct_option = None
        content = (form.content.data or "").strip()

        if post_type in {"voting", "quiz"}:
            raw_options = (form.poll_options.data or "").splitlines()
            options = [item.strip() for item in raw_options if item.strip()]
            if len(options) < 2:
                flash("Voting/Quiz post requires at least 2 answer options.", "warning")
                posts = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
                files = (
                    UploadedFile.query.filter_by(user_id=current_user.id)
                    .order_by(UploadedFile.created_at.desc())
                    .all()
                )
                return render_template("dashboard.html", form=form, posts=posts, files=files)
            poll_options = json.dumps(options, ensure_ascii=False)
            content = "Quiz post" if post_type == "quiz" else "Voting post"
            if post_type == "quiz":
                quiz_correct_option = (form.quiz_correct_option.data or "").strip()
                if quiz_correct_option not in options:
                    flash("For quiz, choose a correct answer from options.", "warning")
                    posts = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
                    files = (
                        UploadedFile.query.filter_by(user_id=current_user.id)
                        .order_by(UploadedFile.created_at.desc())
                        .all()
                    )
                    return render_template("dashboard.html", form=form, posts=posts, files=files)
        elif len(content) < 10:
            flash("Regular post text must be at least 10 characters.", "warning")
            posts = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
            files = (
                UploadedFile.query.filter_by(user_id=current_user.id)
                .order_by(UploadedFile.created_at.desc())
                .all()
            )
            return render_template("dashboard.html", form=form, posts=posts, files=files)

        post = Note(
            title=form.title.data.strip(),
            content=content,
            category=category,
            post_type=post_type,
            poll_type=poll_type,
            poll_options=poll_options,
            quiz_correct_option=quiz_correct_option,
            is_public=form.is_public.data,
            user_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash("Post created.", "success")
        return redirect(url_for("main.dashboard"))
    elif request.method == "POST":
        for field_name, messages in form.errors.items():
            for msg in messages:
                flash(f"{field_name}: {msg}", "warning")

    posts = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    files = (
        UploadedFile.query.filter_by(user_id=current_user.id)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return render_template("dashboard.html", form=form, posts=posts, files=files)


@main_bp.route("/posts/<int:post_id>")
@main_bp.route("/notes/<int:post_id>")
def view_post(post_id: int):
    post = Note.query.get_or_404(post_id)
    if not post.is_public and (not current_user.is_authenticated or current_user.id != post.user_id):
        abort(403)
    user_poll_choice = None
    if current_user.is_authenticated and post.post_type in {"voting", "quiz"}:
        existing = PollResponse.query.filter_by(user_id=current_user.id, post_id=post.id).first()
        user_poll_choice = existing.selected_option if existing else None
    return render_template(
        "notes/detail.html",
        post=post,
        form=CommentForm(),
        user_poll_choice=user_poll_choice,
        poll_counts=post.poll_result_counts(),
    )


@main_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@main_bp.route("/notes/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = Note.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/posts/<int:post_id>/visibility", methods=["POST"])
@main_bp.route("/notes/<int:post_id>/visibility", methods=["POST"])
@login_required
def toggle_post_visibility(post_id: int):
    post = Note.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    post.is_public = not post.is_public
    db.session.commit()
    flash(f"Post is now {'public' if post.is_public else 'private'}.", "success")
    next_url = request.form.get("next")
    if next_url == "detail":
        return redirect(url_for("main.view_post", post_id=post.id))
    return redirect(url_for("main.dashboard"))


@main_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
@main_bp.route("/notes/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id: int):
    post = Note.query.get_or_404(post_id)
    if not post.is_public and post.user_id != current_user.id:
        abort(403)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data.strip(), user_id=current_user.id, note_id=post.id)
        db.session.add(comment)
        db.session.commit()
        flash("Comment added.", "success")
    else:
        flash("Comment is too short.", "warning")
    return redirect(url_for("main.view_post", post_id=post.id))


@main_bp.route("/posts/<int:post_id>/vote", methods=["POST"])
@login_required
def vote_post(post_id: int):
    post = Note.query.get_or_404(post_id)
    value = request.form.get("value", "0")
    if value not in {"1", "-1"}:
        flash("Invalid vote.", "warning")
        return redirect(url_for("main.view_post", post_id=post.id))

    vote_value = int(value)
    existing = PostVote.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        existing.value = vote_value
    else:
        db.session.add(PostVote(user_id=current_user.id, post_id=post.id, value=vote_value))
    db.session.commit()
    flash("Rating updated.", "success")
    return redirect(url_for("main.view_post", post_id=post.id))


@main_bp.route("/posts/<int:post_id>/poll-vote", methods=["POST"])
@login_required
def vote_poll(post_id: int):
    post = Note.query.get_or_404(post_id)
    if post.post_type not in {"voting", "quiz"}:
        flash("This is not a voting/quiz post.", "warning")
        return redirect(url_for("main.view_post", post_id=post.id))

    selected_option = (request.form.get("selected_option") or "").strip()
    options = post.poll_options_list
    if selected_option not in options:
        flash("Please select a valid answer option.", "warning")
        return redirect(url_for("main.view_post", post_id=post.id))

    existing = PollResponse.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        flash("You have already voted. Re-voting is disabled.", "warning")
        return redirect(url_for("main.view_post", post_id=post.id))

    db.session.add(
        PollResponse(
            user_id=current_user.id,
            post_id=post.id,
            selected_option=selected_option,
        )
    )
    db.session.commit()

    if post.poll_type == "quiz" and post.quiz_correct_option:
        if selected_option == post.quiz_correct_option:
            flash("Correct answer!", "success")
        else:
            flash("Answer saved. Try again if needed.", "info")
    else:
        flash("Your vote has been saved.", "success")
    return redirect(url_for("main.view_post", post_id=post.id))


@main_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("File not selected.", "warning")
        return redirect(url_for("main.dashboard"))

    if not is_allowed_file(file.filename):
        flash("Invalid file type.", "danger")
        return redirect(url_for("main.dashboard"))

    original_name, stored_name = save_uploaded_file(file)
    saved_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    meta = UploadedFile(
        original_name=original_name,
        stored_name=stored_name,
        mime_type=file.mimetype or "application/octet-stream",
        size_bytes=os.path.getsize(saved_path),
        user_id=current_user.id,
    )
    db.session.add(meta)
    db.session.commit()
    flash(f"File {original_name} uploaded.", "success")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/files/<int:file_id>")
@login_required
def download_file(file_id: int):
    file = UploadedFile.query.get_or_404(file_id)
    if file.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], file.stored_name, as_attachment=True
    )
