# Budget Dictionaries API — backend

Самостоятельный пример модуля справочников и правил распределения из командного проекта: категории, бюджетные статьи, ЦФО, МРП и организации. Python 3.14, uv. Название Python-пакета `sigma` сохранено.

Область примера, разграничение авторства и ограничения описаны в [основном README](../README.md).

## Команды

```bash
uv sync                  # поставить зависимости
uv run uvicorn sigma.main:app --reload   # запуск API (FastAPI)

# Миграции (alembic, конфиг в alembic.ini, среда в migrations/)
uv run alembic revision --autogenerate -m "описание"   # новая миграция по моделям
uv run alembic upgrade head        # накатить
uv run alembic downgrade -1        # откатить на шаг

uv run ruff check sigma tests    # линт (вкл. сложность: C901, PLR09xx, FAST)
uv run ruff format sigma tests   # форматирование
uv run basedpyright sigma tests  # проверка типов
uv run pytest                    # тесты (зеркалят структуру sigma/)
uv run pytest -m postgres        # интеграционные тесты; нужен SIGMA_TEST_DATABASE_URL
uv run lint-imports              # архитектурные контракты (границы модулей)

# Метрики сложности
uv run complexipy          # когнитивная сложность (гейт), настройки в pyproject.toml
uv run complexipy --output-format json --output complexity-report.json   # отчёт в JSON
```

## Окружение

Настройки — через переменные окружения (pydantic-settings, `.env` поддерживается):

- `DATABASE_URL` — по умолчанию `postgresql+asyncpg://postgres:postgres@localhost:5432/sigma`
- `JSON_LOGS` — `true` для JSON-логов (прод), по умолчанию цветной вывод (structlog)
