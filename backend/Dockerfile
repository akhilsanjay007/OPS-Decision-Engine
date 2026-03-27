FROM python:3.11-slim

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=${APP_HOME}

# Install Python dependencies first for better layer caching.
COPY backend/requirements.txt ${APP_HOME}/requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch==2.4.1"
RUN pip install --no-cache-dir --upgrade-strategy only-if-needed -r ${APP_HOME}/requirements.txt

# Copy application and runtime assets.
COPY backend/src/ ${APP_HOME}/src/
COPY backend/app/ ${APP_HOME}/app/
COPY backend/models/ ${APP_HOME}/models/
COPY backend/data/processed/ ${APP_HOME}/data/processed/
RUN mkdir -p ${APP_HOME}/data/chroma

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

