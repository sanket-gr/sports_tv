FROM mcr.microsoft.com/playwright/python:v1.60.0-jammy


WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000 for Uvicorn
EXPOSE 8000

# Set environment variables for production
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

# Start the FastAPI application
# (In production we run migrations first to ensure DB is up to date)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"]
