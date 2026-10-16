# sigma

Система управления экономией. Python 3.14, uv.

**S**avings **I**nsights & **G**rowth **MA**nagement

«СИГМА»: **С**бережения, **И**нсайты (аналитика), **Г**рамотное **М**аневрирование **А**ктивами

## Команды

```bash
uv sync                  # поставить зависимости
uv run uvicorn sigma.main:app --reload   # запуск API (FastAPI)

uv run ruff check sigma tests    # линт (вкл. сложность: C901, PLR09xx, FAST)
uv run ruff format sigma tests   # форматирование
uv run basedpyright sigma tests  # проверка типов
uv run pytest                    # тесты (зеркалят структуру sigma/)
uv run lint-imports              # архитектурные контракты (границы модулей)

# Метрики сложности
uv run complexipy          # когнитивная сложность (гейт), настройки в pyproject.toml
uv run complexipy --output-format json --output complexity-report.json   # отчёт в JSON
```

## Окружение

Настройки — через переменные окружения (pydantic-settings, `.env` поддерживается):

- `DATABASE_URL` — по умолчанию `postgresql+asyncpg://postgres:postgres@localhost:5432/sigma`
- `JSON_LOGS` — `true` для JSON-логов (прод), по умолчанию цветной вывод (structlog)
