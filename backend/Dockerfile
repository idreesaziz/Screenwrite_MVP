FROM python:3.12-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

# Create output directory for media files
RUN mkdir -p /app/out

EXPOSE 3000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
