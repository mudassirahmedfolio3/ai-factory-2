FROM python:3.12-slim

WORKDIR /app

COPY ai_factory/pyproject.toml ai_factory/README.md /app/ai_factory/
COPY ai_factory/src /app/ai_factory/src
COPY ai_factory_ui/api /app/ai_factory_ui/api

RUN pip install --no-cache-dir \
    "crewai[tools]" \
    fastapi uvicorn sse-starlette python-dotenv pydantic

WORKDIR /app/ai_factory_ui/api
ENV PYTHONPATH=/app/ai_factory/src:/app/ai_factory_ui/api

EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
