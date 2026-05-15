from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError

from models import User


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("This username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("This email is already in use.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=120)])
    content = TextAreaField("Post text", validators=[Length(max=5000)])
    category = SelectField(
        "Category",
        choices=[
            ("general", "General"),
            ("study", "Study"),
            ("work", "Work"),
            ("ideas", "Ideas"),
            ("yandexlms", "YandexLMS"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    custom_category = StringField("Custom category", validators=[Length(max=50)])
    post_type = SelectField(
        "Post type",
        choices=[("regular", "Regular"), ("voting", "Voting"), ("quiz", "Quiz")],
        validators=[DataRequired()],
    )
    poll_options = TextAreaField(
        "Answer options (one per line)",
        validators=[Length(max=4000)],
    )
    quiz_correct_option = SelectField(
        "Correct answer",
        choices=[("", "Select correct option")],
        validate_choice=False,
    )
    is_public = BooleanField("Public post")


class CommentForm(FlaskForm):
    body = TextAreaField("Comment", validators=[DataRequired(), Length(min=2, max=1000)])
