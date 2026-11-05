FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python server.py --prepare-only \
    && useradd --uid 10001 --create-home course \
    && mkdir -p /app/data \
    && chown -R course:course /app
USER course
ENV HOST=0.0.0.0 PORT=8876 TEACHU_DATA_DIR=/app/data PYTHONUNBUFFERED=1
EXPOSE 8876
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8876/api/account', timeout=3)"
CMD ["python", "server.py"]
