FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models-cache

WORKDIR /app

# CPU-only PyTorch (about 2 GB smaller than the default CUDA build)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

# models/models.txt and data/ are mounted by docker-compose, so they are not copied here
COPY app ./app

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]