FROM python:3.10-slim

# Install system dependencies including ffmpeg for video/audio remuxing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create downloads directory
RUN mkdir -p Downloaded_Videos

# Expose default web port
EXPOSE 5000

# Start Flask server
CMD ["python", "app.py"]
