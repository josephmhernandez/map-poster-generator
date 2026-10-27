FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TILE_ENGINE_PNG_ONLY=1

WORKDIR /app
COPY requirements-container.txt ./
RUN pip install --no-cache-dir -r requirements-container.txt
COPY . .
CMD ["python", "ecs_worker.py"]
