FROM python:3.10

# Set up a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Stage files with correct ownership
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=user . .

EXPOSE 7860
CMD ["python", "app.py"]

