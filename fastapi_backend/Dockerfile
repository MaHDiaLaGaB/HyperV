# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# 1) Copy only dependencies, install globally
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Copy application code
COPY . .

# 3) Expose port and run
EXPOSE 8000

# COPY start.sh .
ENTRYPOINT ["./start.sh"]