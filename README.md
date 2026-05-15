# StudyForum (Flask Project)

Учебный WEB-проект на Flask в формате форума с постами, голосованиями, викторинами, рейтингом и REST API.

## Функционал

- Регистрация и авторизация пользователей (`Flask-Login`).
- Форумные посты:
  - `Regular` (обычный текстовый пост),
  - `Voting` (опрос с вариантами ответа),
  - `Quiz` (викторина с правильным ответом).
- Категории постов:
  - стандартные + `Other` (свой вариант) + `YandexLMS`.
- Комментарии к постам.
- Рейтинг постов (лайк/дизлайк).
- Голосование в опросах:
  - выбор 1 варианта,
  - повторное голосование запрещено,
  - отображение количества и процентов по вариантам.
- Викторина:
  - подсветка ответа после выбора (неверный — красный, верный — зеленый).
- Управление приватностью поста:
  - переключение `Private/Public`,
  - удаление своих постов.
- Загрузка и скачивание файлов.
- REST API + интеграция со сторонним API погоды (Open-Meteo).
- Рендер кода в тексте по тройным кавычкам ```...```:
  - подсветка синтаксиса,
  - отдельный code-блок,
  - кнопка `Copy`.

## Технологии

- Flask
- Flask-SQLAlchemy (ORM)
- Flask-WTF (формы и валидация)
- Flask-Login (сессии)
- Bootstrap 5
- SQLite
- highlight.js

## Быстрый запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Открыть: `http://127.0.0.1:5000`

## API (основное)

- `GET /api/health`
- `GET /api/posts/public`
- `GET /api/posts/my` (auth)
- `POST /api/posts` (auth)
- `GET /api/posts/<id>/comments`
- `POST /api/posts/<id>/comments` (auth)
- `POST /api/posts/<id>/vote` (auth, рейтинг)
- `GET /api/weather?city=Vladivostok`

## Структура проекта

- `app.py` — запуск приложения, создание таблиц, авто-обновление схемы SQLite.
- `models.py` — ORM-модели (`User`, `Note`, `Comment`, `PostVote`, `PollResponse`, `UploadedFile`).
- `forms.py` — формы.
- `routes/` — маршруты web/API/auth.
- `services/` — сервисная логика (файлы, погода).
- `templates/`, `static/` — интерфейс и клиентские скрипты.
