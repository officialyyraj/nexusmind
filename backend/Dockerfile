FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create directories
RUN mkdir -p /app/workspace /app/plugins /app/data
# Change ownership of directories that need to be writable at runtime
RUN chown -R appuser:appuser /app/workspace /app/plugins /app/data

# Make startup script executable
RUN chmod +x /app/startup.sh

# Switch to the non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV AUTO_GENERATE_SECRETS=true
ENV RUN_MIGRATIONS=true

# Expose port
EXPOSE 8000

# Run the application via startup script
CMD ["/app/startup.sh", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
