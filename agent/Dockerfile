FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY agent/requirements.txt /app/agent/requirements.txt
RUN pip install --no-cache-dir -r /app/agent/requirements.txt

# Copy agent package
COPY agent /app/agent

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run ADK Web / API Server on Cloud Run (deploy with --min-instances=1 to avoid cold starts)
CMD ["sh", "-c", "adk web --host 0.0.0.0 --port ${PORT} /app"]

