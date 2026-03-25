FROM python:3.11-slim

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=${APP_HOME}

# Install Python dependencies first for better layer caching.
COPY requirements.txt ${APP_HOME}/requirements.txt
RUN pip install --no-cache-dir -r ${APP_HOME}/requirements.txt

# Copy application and runtime assets.
COPY src/ ${APP_HOME}/src/
COPY app/ ${APP_HOME}/app/
COPY models/ ${APP_HOME}/models/
COPY data/ ${APP_HOME}/data/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

