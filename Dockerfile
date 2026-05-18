FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py products.json ./
COPY templates ./templates

RUN useradd --create-home --shell /bin/bash --uid 1000 app \
 && mkdir -p /data \
 && chown -R app:app /app /data
USER app

VOLUME /data

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/health').status == 200 else 1)" || exit 1

CMD ["python", "app.py"]
