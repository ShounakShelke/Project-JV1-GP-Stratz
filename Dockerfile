FROM python:3.10-slim

WORKDIR /app

# Copy requirement list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all local project files to container
COPY . .

# Run the grader as the default entrypoint
CMD ["python", "grader/evaluate.py"]
