FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "sleep 8 && python -c \"import asyncio; from app.core.database import init_db; asyncio.run(init_db())\" && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
