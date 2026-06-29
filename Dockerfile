# Dockerfile for Dbus Logger Frontend
# Multi-platform support (amd64, arm64, armv7)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "start_frontend.py", "--no-browser"]
