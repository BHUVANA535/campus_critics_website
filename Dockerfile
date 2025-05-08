# Use a slim Python base image
FROM python:3.11-slim

# Install basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run the app with Gunicorn
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
