FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the requirements file
COPY api/requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc python3-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Command to run the application using gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT "api.app:create_app()"
