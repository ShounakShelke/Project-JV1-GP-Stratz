FROM python:3.10

ENV ENABLE_WEB_INTERFACE=true
ENV PORT=8000

# Set up a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .

EXPOSE 8000

CMD ["python", "app.py"]
