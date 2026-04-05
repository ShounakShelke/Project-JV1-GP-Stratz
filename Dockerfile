FROM python:3.10-slim

ENV ENABLE_WEB_INTERFACE=true
ENV PORT=8000

WORKDIR /app

# Copy requirement list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt uv

# Copy all local project files to container
COPY . .

# Run the app from root
CMD ["python", "app.py"]
