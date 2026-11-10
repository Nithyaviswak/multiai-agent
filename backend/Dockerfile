FROM python:3.12-slim

# Fail fast, keep logs unbuffered, avoid writing .pyc files into the image.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Run as an unprivileged user. The app keeps all state in memory, so there is
# nothing to persist on disk.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home app

# Dependencies first so source changes do not invalidate the pip layer.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

USER app

EXPOSE 8000

# Uses only the Python stdlib so the image does not need curl.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)"

# IMPORTANT: keep a single worker. Workflow state, the key ring, the active
# model and rate-limit buckets are held in process memory, so running multiple
# workers would make requests hit inconsistent state. Scale vertically or
# introduce shared storage before raising --workers.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
