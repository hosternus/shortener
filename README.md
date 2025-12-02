# URL Shortener API

Небольшой сервис на FastAPI, который сокращает ссылки, хранит их в базе через SQLAlchemy и предоставляет статистику переходов. Приложение автоматически создаёт таблицы при старте и может работать как в локальной среде разработчика, так и внутри Docker-контейнера.

## Возможности
- Создание коротких ссылок (`POST /url`) с гарантией уникальности `short_id`.
- Редирект на исходный адрес по короткому идентификатору (`GET /{short_id}`) с учётом счётчика переходов.
- Получение статистики по ссылке (`GET /{short_id}/stats`) с числом визитов и временными метками.
- Возможность подключить Redis-кеш (закомментировано в коде, чтобы включить достаточно задать `REDIS_CACHE_URL` и раскомментировать блок в `main.py`).

## Требования
- Python 3.11+ (Dockerfile использует образ `python:3.13-slim`).
- Любая БД, поддерживаемая SQLAlchemy (PostgreSQL, SQLite и пр.).
- Установленные зависимости из `requirements.txt`.

## Переменные окружения
Создайте файл `.env` или передайте значения снаружи (Pydantic Settings подхватывает переменные среды).

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `DATABASE_URL` | Да | Строка подключения SQLAlchemy. Примеры: `sqlite+aiosqlite:///./db.sqlite3`, `postgresql+psycopg://user:pass@host:5432/db`. |
| `BASE_URL` | Да | Базовый URL, который используется для сборки полного короткого адреса в ответе (например, `https://sho.rt/`). |
| `REDIS_CACHE_URL` | Нет | Подключение к Redis, если планируете включить кеширование ответов FastAPI Cache. |

## Локальный запуск
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./db.sqlite3"
export BASE_URL="http://localhost:8000/"
uvicorn main:app --reload
```
FastAPI по умолчанию доступен на `http://localhost:8000`. Для запуска встроенного продакшен-сервера можно использовать `python main.py` (стартует на `0.0.0.0:80`).

## Запуск в Docker
```bash
docker build -t url-shortener .
docker run -p 8000:80 \
  -e DATABASE_URL="postgresql+psycopg://user:pass@db:5432/short" \
  -e BASE_URL="http://localhost:8000/" \
  url-shortener
```
Таблицы создаются автоматически при старте контейнера.

## API
Все ответы и запросы валидируются моделями из `schemas.py`.

### POST /url
Создаёт короткую ссылку или возвращает уже существующую.
```bash
curl -X POST http://localhost:8000/url \
  -H "Content-Type: application/json" \
  -d '{"source_url": "https://example.com/articles/42"}'
```
Пример ответа:
```json
{
  "source_url": "https://example.com/articles/42",
  "short_id": "Ab3F9xYz",
  "full_url": "http://localhost:8000/Ab3F9xYz",
  "visits": 0,
  "created_at": "2024-10-01T12:00:00",
  "updated_at": "2024-10-01T12:00:00"
}
```

### GET /{short_id}
Редиректит пользователя на исходную ссылку и увеличивает счётчик посещений.

### GET /{short_id}/stats
Возвращает JSON аналогичный `ShortedURLResponse`, включающий `visits`, `created_at` и `updated_at`.

## Структура проекта
- `main.py` — точки входа FastAPI, маршруты и жизненный цикл приложения.
- `database/` — модели, создание engine и CRUD-helpers.
- `schemas.py` — Pydantic-модели запросов/ответов.
- `utils.py` — генерация коротких идентификаторов.
- `Dockerfile` — образ для продакшена.

## Дополнительно
- Чтобы включить кеширование, настройте `REDIS_CACHE_URL` и раскомментируйте блок с `FastAPICache` в `main.py`.
- Pydantic и SQLAlchemy логируют ошибки, поэтому при отладке полезно выставить `LOGLEVEL=INFO` (например, через `uvicorn main:app --reload --log-level info`).
