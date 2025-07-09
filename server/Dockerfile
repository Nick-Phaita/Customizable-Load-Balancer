FROM python:3.12-slim

# Avoid generating .pyc files and make stdout flush immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]
