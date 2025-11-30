FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN apt-get update && apt-get install -y iputils-ping curl
RUN ping -c 4 pypi.org
RUN curl -I https://pypi.org
RUN cat /etc/resolv.conf

RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Set Python path
ENV PYTHONPATH=/app

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
