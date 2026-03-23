FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY aegis_gov/ aegis_gov/

EXPOSE 8000

CMD ["uvicorn", "aegis_gov.api:app", "--host", "0.0.0.0", "--port", "8000"]
