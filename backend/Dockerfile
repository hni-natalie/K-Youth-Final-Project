FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --frozen --no-dev

# Copy source code into a 'backend' package so imports like
# 'from backend.api.routes import ...' resolve correctly
RUN mkdir -p backend
COPY api/ ./backend/api/
COPY core/ ./backend/core/
COPY utils/ ./backend/utils/
COPY pipeline/ ./backend/pipeline/

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
