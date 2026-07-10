FROM python:3.11-slim
WORKDIR /app
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/qckit backend/qckit
RUN pip install --no-cache-dir -e ./backend
COPY backend/static /app/backend/static
EXPOSE 8000
CMD ["uvicorn", "qckit.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
