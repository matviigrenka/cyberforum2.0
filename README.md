# StudyHub (Flask Project)

Учебный WEB-проект на Flask для максимального покрытия критериев: архитектура, технологии, оформление и демонстрация.

## Что реализовано

- Flask-приложение с модульной структурой (`routes`, `services`, `models`).
- ORM через `Flask-SQLAlchemy` (модели `User`, `Note`, `UploadedFile`).
- Регистрация, авторизация, сессии (`Flask-Login`).
- Формы и валидация (`Flask-WTF`).
- Загрузка и скачивание файлов.
- REST API:
  - `GET /api/health`
  - `GET /api/notes/public`
  - `GET /api/notes/my` (auth)
  - `POST /api/notes` (auth)
  - `GET /api/weather?city=Vladivostok` (сторонний API Open-Meteo)
- Хранение данных в SQLite.
- Интерфейс на Bootstrap 5.

## Быстрый запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Открыть: `http://127.0.0.1:5000`

## Минимальная структура

- `app.py` — точка входа и фабрика приложения.
- `config.py` — конфигурация.
- `extensions.py` — инициализация расширений.
- `models.py` — ORM-модели.
- `forms.py` — формы.
- `routes/` — блюпринты.
- `services/` — бизнес-логика (файлы, погода).
- `templates/`, `static/` — фронтенд.

## Что показать на защите

- Демонстрация регистрации/входа.
- Создание/удаление заметок, публичные заметки на главной.
- Загрузка и скачивание файла.
- Работа API (например через браузер/Postman).
- Вызов стороннего API погоды.

## Идеи для доработки (премия/оригинальность)

- Роли преподаватель/студент с разграничением доступа.
- Комментарии к заметкам.
- Поиск и фильтрация.
- Docker + деплой на Render/Railway.
