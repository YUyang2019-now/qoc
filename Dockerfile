FROM python:3.12-slim AS runtime

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
COPY frontend/dist /app/frontend/dist

ENV QOC_DATA_DIR=/data
EXPOSE 8000
CMD ["sh", "-c", "cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
