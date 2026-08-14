FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the requirements file
COPY api/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Command to run the application using gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT "api.app:create_app()"
