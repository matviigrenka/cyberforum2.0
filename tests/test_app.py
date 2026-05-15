from io import BytesIO

import pytest

from app import create_app
from extensions import db
from models import Note, User


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="tester", email="tester@example.com", password="secret12"):
    return client.post(
        "/auth/register",
        data={"username": username, "email": email, "password": password},
        follow_redirects=True,
    )


def login(client, email="tester@example.com", password="secret12"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_index_works(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "StudyHub".encode("utf-8") in response.data


def test_register_and_login(client):
    r = register(client)
    assert r.status_code == 200
    assert "Регистрация прошла успешно".encode("utf-8") in r.data

    r2 = login(client)
    assert r2.status_code == 200
    assert "Вы вошли в аккаунт".encode("utf-8") in r2.data


def test_dashboard_requires_auth(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in {302, 401}


def test_create_note_via_form(client, app):
    register(client)
    login(client)

    response = client.post(
        "/dashboard",
        data={
            "title": "My First Note",
            "content": "This is a long enough content for a test note.",
            "category": "study",
            "is_public": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Заметка создана".encode("utf-8") in response.data

    with app.app_context():
        assert Note.query.count() == 1
        assert Note.query.first().is_public is True


def test_create_note_via_api(client, app):
    register(client)
    login(client)

    response = client.post(
        "/api/notes",
        json={"title": "API Note", "content": "Content from JSON body for test", "category": "ideas"},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["item"]["title"] == "API Note"

    with app.app_context():
        assert Note.query.count() == 1


def test_public_notes_api(client, app):
    with app.app_context():
        user = User(username="alex", email="alex@example.com")
        user.set_password("secret12")
        db.session.add(user)
        db.session.commit()
        db.session.add(
            Note(
                title="Public Note",
                content="Useful text for all students.",
                category="general",
                is_public=True,
                user_id=user.id,
            )
        )
        db.session.commit()

    response = client.get("/api/notes/public")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "Public Note"


def test_upload_file(client, app):
    register(client)
    login(client)

    data = {"file": (BytesIO(b"hello world"), "sample.txt")}
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert "загружен".encode("utf-8") in response.data.lower()


def test_comment_flow(client, app):
    register(client, username="mike", email="mike@example.com")
    login(client, email="mike@example.com")

    client.post(
        "/dashboard",
        data={
            "title": "Share",
            "content": "Public note for comments testing.",
            "category": "study",
            "is_public": "y",
        },
        follow_redirects=True,
    )

    with app.app_context():
        note = Note.query.first()
        assert note is not None
        note_id = note.id

    response = client.post(
        f"/api/notes/{note_id}/comments",
        json={"body": "Nice note"},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["item"]["body"] == "Nice note"

    response2 = client.get(f"/api/notes/{note_id}/comments")
    assert response2.status_code == 200
    assert len(response2.get_json()["items"]) == 1
