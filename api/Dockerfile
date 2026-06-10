FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source directories are volume-mounted in dev; copied here for production builds.
COPY api/ ./api/
COPY extraction/ ./extraction/

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
