FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-test.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-test.txt pytest

# Copy application code
COPY . .

# Add application directory to Python path
ENV PYTHONPATH=/app

EXPOSE 5000

# Default command (can be overridden)
CMD ["python", "app.py"] 